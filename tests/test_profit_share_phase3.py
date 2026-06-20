"""Phase 3 — profit-share calculation service (pure).

Verifies the exact cascade math, contract sourcing (estimate + COs), the
guards (contract<=0), the 40/60 split, negative net at close, and the CRITICAL
rule that socios are never counted as project labor cost.
"""
from __future__ import annotations

from datetime import date, time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core import access
from core.models import (
    ChangeOrder,
    CostCode,
    Employee,
    Estimate,
    EstimateLine,
    Expense,
    Project,
    RateConfig,
    TimeEntry,
)
from core.services.profit_share_service import (
    compute_contract_amount,
    compute_project_financials,
)

User = get_user_model()


@pytest.fixture
def rates():
    """Singleton RateConfig with documented defaults."""
    return RateConfig.load()


def _project(**kw):
    defaults = dict(
        name="PS Calc Project",
        budget_total=Decimal("100000.00"),
        budget_materials=Decimal("20000.00"),
        budget_labor=Decimal("30000.00"),
    )
    defaults.update(kw)
    return Project.objects.create(**defaults)


@pytest.mark.django_db
class TestContractAmount:
    def test_fallback_to_budget_total_when_no_estimate(self):
        p = _project(budget_total=Decimal("75000.00"))
        assert compute_contract_amount(p) == Decimal("75000.00")

    def test_uses_approved_estimate_total(self):
        p = _project(budget_total=Decimal("1.00"))
        cc = CostCode.objects.create(code="CC-1", name="Labor")
        est = Estimate.objects.create(project=p, version=1, approved=True)
        EstimateLine.objects.create(
            estimate=est, cost_code=cc, qty=Decimal("10"), unit_price=Decimal("1000")
        )  # total_price = 10,000
        assert compute_contract_amount(p) == Decimal("10000.00")

    def test_adds_approved_fixed_change_orders(self):
        p = _project(budget_total=Decimal("50000.00"))
        ChangeOrder.objects.create(
            project=p, description="CO1", amount=Decimal("5000"),
            pricing_type="FIXED", status="approved",
        )
        ChangeOrder.objects.create(
            project=p, description="CO2 draft", amount=Decimal("9999"),
            pricing_type="FIXED", status="draft",  # excluded
        )
        assert compute_contract_amount(p) == Decimal("55000.00")


@pytest.mark.django_db
class TestCascadeMath:
    def test_exact_cascade_with_defaults(self, rates):
        """contract 100k, materials 20k (est), labor 30k (est), 2 socios."""
        p = _project()
        f = compute_project_financials(p, use_actuals=False, active_socios=2)
        assert f.contract_amount == Decimal("100000.00")
        assert f.materials == Decimal("20000.00")
        assert f.other_labor == Decimal("30000.00")
        assert f.company_overhead == Decimal("8000.00")
        assert f.direction_overhead == Decimal("8000.00")
        assert f.callback_reserve == Decimal("5000.00")
        assert f.bad_debt_reserve == Decimal("500.00")
        assert f.net == Decimal("28500.00")
        assert f.director_share == Decimal("11400.00")
        assert f.partner_pool == Decimal("17100.00")
        assert f.per_socio == Decimal("8550.00")
        assert f.active_socios == 2
        assert f.can_accrue is True
        assert f.direction_overhead_destination == RateConfig.DESTINATION_BUSINESS

    def test_per_socio_zero_when_no_socios(self):
        p = _project()
        f = compute_project_financials(p, use_actuals=False, active_socios=0)
        assert f.per_socio == Decimal("0.00")
        assert f.partner_pool == Decimal("17100.00")  # pool still computed

    def test_director_plus_pool_equals_net(self):
        p = _project()
        f = compute_project_financials(p, use_actuals=False, active_socios=2)
        assert f.director_share + f.partner_pool == f.net


@pytest.mark.django_db
class TestGuards:
    def test_zero_contract_cannot_accrue(self):
        p = _project(budget_total=Decimal("0.00"))
        f = compute_project_financials(p, use_actuals=False, active_socios=2)
        assert f.contract_amount == Decimal("0.00")
        assert f.can_accrue is False
        assert f.net == Decimal("0.00")
        assert f.director_share == Decimal("0.00")
        assert f.per_socio == Decimal("0.00")


@pytest.mark.django_db
class TestNegativeNetAtClose:
    def test_real_loss_shares_negative(self, rates):
        """A closed project with huge actual costs → negative net → socios
        share the loss (congruent with 'rendimiento espantoso')."""
        p = _project(budget_total=Decimal("10000.00"),
                     budget_materials=Decimal("0"), budget_labor=Decimal("0"))
        # Actual material expense dwarfs the contract.
        Expense.objects.create(
            project=p, project_name=p.name, amount=Decimal("50000.00"),
            date=date.today(), category="MATERIALES",
        )
        f = compute_project_financials(p, use_actuals=True, active_socios=2)
        assert f.contract_amount == Decimal("10000.00")
        assert f.can_accrue is True
        assert f.materials == Decimal("50000.00")
        assert f.net < 0
        assert f.director_share < 0
        assert f.per_socio < 0


@pytest.mark.django_db
class TestSocioExcludedFromLaborCost:
    def _emp(self, ssn, rate, user=None):
        return Employee.objects.create(
            first_name="T", last_name=ssn, social_security_number=ssn,
            hourly_rate=Decimal(rate), user=user,
        )

    def _time(self, emp, project, hours_start=time(8, 0), hours_end=time(18, 0)):
        return TimeEntry.objects.create(
            employee=emp, project=project, date=date.today(),
            start_time=hours_start, end_time=hours_end,
        )

    def test_socio_time_not_counted_as_labor(self):
        p = _project(budget_total=Decimal("100000.00"))
        # Normal crew: rate 50 × hours (hours derived from TimeEntry, which may
        # deduct an unpaid lunch — we read the persisted value to stay robust).
        crew = self._emp("SSN-CREW-1", "50.00")
        crew_te = self._time(crew, p)
        crew_te.refresh_from_db()
        expected = (crew_te.hours_worked * Decimal("50.00")).quantize(Decimal("0.01"))
        # Socio: linked to a partner user; rate 100 (must be excluded entirely)
        socio_user = User.objects.create_user("calc_socio", password="x")
        socio_user.profile.role = access.ROLE_PARTNER
        socio_user.profile.save()
        socio_emp = self._emp("SSN-SOCIO-1", "100.00", user=socio_user)
        self._time(socio_emp, p)

        f = compute_project_financials(p, use_actuals=True, active_socios=2)
        # Only the crew's labor counts; the socio's hours are excluded.
        assert f.other_labor == expected

    def test_crew_without_user_is_included(self):
        p = _project(budget_total=Decimal("100000.00"))
        crew = self._emp("SSN-CREW-2", "40.00")  # no user
        crew_te = self._time(crew, p)
        crew_te.refresh_from_db()
        expected = (crew_te.hours_worked * Decimal("40.00")).quantize(Decimal("0.01"))
        f = compute_project_financials(p, use_actuals=True, active_socios=2)
        assert f.other_labor == expected
        assert f.other_labor > 0  # crew without a user IS included
