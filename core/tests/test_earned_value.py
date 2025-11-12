from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from core.models import Project, CostCode, BudgetLine, BudgetProgress, Expense
from core.services.earned_value import compute_project_ev

class EarnedValueTests(TestCase):
    def setUp(self):
        self.start = date(2025, 8, 20)
        self.finish = date(2025, 8, 30)

        # Project con campos requeridos
        self.project = Project.objects.create(
            name="Test Project",
            start_date=self.start,
            end_date=self.finish,
        )

        self.cc = CostCode.objects.create(code="LAB001", name="Labor")

        self.line = BudgetLine.objects.create(
            project=self.project,
            cost_code=self.cc,
            description="Test Line",
            qty=Decimal("10"),
            unit_cost=Decimal("100"),
            planned_start=self.start,
            planned_finish=self.finish,
        )
        # Garantiza baseline por si tu modelo no lo calcula en save()
        if not self.line.baseline_amount:
            self.line.baseline_amount = self.line.qty * self.line.unit_cost
            self.line.save(update_fields=["baseline_amount"])
        self.baseline = self.line.baseline_amount

    def test_pv_linear(self):
        s0 = compute_project_ev(self.project, as_of=self.start)
        self.assertEqual(s0["PV"], Decimal("0"))
        mid = self.start + timedelta(days=5)
        s_mid = compute_project_ev(self.project, as_of=mid)
        self.assertAlmostEqual(float(s_mid["PV"]), float(self.baseline * Decimal("0.5")), places=2)
        end = self.finish + timedelta(days=1)
        s_end = compute_project_ev(self.project, as_of=end)
        self.assertAlmostEqual(float(s_end["PV"]), float(self.baseline), places=2)

    def test_ev_from_progress(self):
        prog_date = self.start + timedelta(days=3)
        BudgetProgress.objects.create(
            budget_line=self.line,
            date=prog_date,
            percent_complete=Decimal("30"),
            qty_completed=Decimal("0"),
        )
        as_of = self.start + timedelta(days=6)
        s = compute_project_ev(self.project, as_of=as_of)
        expected_ev = self.baseline * Decimal("0.30")
        self.assertAlmostEqual(float(s["EV"]), float(expected_ev), places=2)

    def test_ac_from_expense(self):
        # Gasto antes del corte cuenta
        Expense.objects.create(
            project=self.project,
            amount=Decimal("400"),
            date=self.start + timedelta(days=2),
            description="Test"  # si tu modelo requiere otro campo, ajusta aquí
        )
        # Gasto posterior al corte NO cuenta
        Expense.objects.create(
            project=self.project,
            amount=Decimal("999"),
            date=self.finish + timedelta(days=10),
            description="Later"
        )
        s = compute_project_ev(self.project, as_of=self.start + timedelta(days=3))
        self.assertAlmostEqual(float(s["AC"]), 400.0, places=2)

    def test_spi_cpi(self):
        # Progreso 50% y costo real 400; al día después del finish PV=100%
        BudgetProgress.objects.create(
            budget_line=self.line,
            date=self.start + timedelta(days=4),
            percent_complete=Decimal("50"),
            qty_completed=0,
        )
        Expense.objects.create(
            project=self.project,
            amount=Decimal("400"),
            date=self.finish,
            description="Cost"
        )
        as_of = self.finish + timedelta(days=1)
        s = compute_project_ev(self.project, as_of=as_of)

        self.assertAlmostEqual(float(s["EV"]), float(self.baseline * Decimal("0.5")), places=2)
        self.assertAlmostEqual(float(s["PV"]), float(self.baseline), places=2)
        self.assertAlmostEqual(float(s["AC"]), 400.0, places=2)
        self.assertAlmostEqual(float(s["SPI"]), 0.5, places=2)
        self.assertAlmostEqual(
            float(s["CPI"]),
            float((self.baseline * Decimal("0.5")) / Decimal("400")),
            places=2
        )