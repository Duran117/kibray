import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import RFI, DamageReport, Employee, Expense, FloorPlan, Income, Issue, Project, Risk, TimeEntry


@pytest.fixture
def staff_client(db):
    """Return an isolated authenticated client not tied to the default 'client' fixture.

    This avoids tests that also request the 'client' fixture from accidentally
    sharing authentication state via fixture dependency graphs.
    """
    user = User.objects.create_user(username="admin", password="pass", is_staff=True)
    c = Client()
    assert c.login(username="admin", password="pass")
    return c


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Proj A",
        start_date=timezone.now().date(),
    )


@pytest.fixture
def floor_plan(db, project):
    # Minimal 1x1 PNG bytes
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0bIDAT\x08\x99c```\x00\x00\x00\x05\x00\x01"
        b"\x0d\x0a\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    image = SimpleUploadedFile("tiny.png", png_bytes, content_type="image/png")
    return FloorPlan.objects.create(
        project=project,
        name="Level 0",
        level=0,
        image=image,
    )


@pytest.fixture
def damage_report(db, project, staff_client):
    # Create a report by the same staff user to simplify permissions
    user = User.objects.get(username="admin")
    return DamageReport.objects.create(
        project=project,
        title="Crack on wall",
        description="Small crack",
        reported_by=user,
    )


@pytest.fixture
def income(db, project):
    return Income.objects.create(
        project=project,
        project_name="Invoice 001",
        amount=1000,
        date=timezone.now().date(),
        payment_method="EFECTIVO",
    )


@pytest.fixture
def expense(db, project):
    return Expense.objects.create(
        project=project,
        amount=250,
        project_name="Mat purchases",
        date=timezone.now().date(),
        category="MATERIALES",
    )


@pytest.fixture
def employee(db):
    # Attach to admin user created in staff_client
    user = User.objects.get(username="admin")
    return Employee.objects.create(
        user=user,
        first_name="Admin",
        last_name="User",
        social_security_number="123-45-6789",
        hourly_rate=25.00,
        email="admin@example.com",
    )


@pytest.fixture
def timeentry(db, project, employee):
    from datetime import date, time

    return TimeEntry.objects.create(
        employee=employee,
        project=project,
        date=date.today(),
        start_time=time(8, 0),
        end_time=time(17, 0),
        notes="Demo entry",
    )


@pytest.fixture
def rfi(db, project):
    return RFI.objects.create(
        project=project,
        number=1,
        question="What is the wall height?",
        status="open",
    )


@pytest.fixture
def issue(db, project):
    return Issue.objects.create(
        project=project,
        title="Cracked tile",
        description="Tile in bathroom has crack",
        severity="medium",
        status="open",
    )


@pytest.fixture
def risk(db, project):
    return Risk.objects.create(
        project=project,
        title="Rain delay",
        probability=30,
        impact=50,
        mitigation="Monitor weather and adjust schedule accordingly",
        status="identified",
    )


@pytest.mark.django_db
class TestSmokeRoutes:
    def test_income_expense_lists(self, staff_client):
        assert staff_client.get(reverse("income_list")).status_code == 200
        assert staff_client.get(reverse("expense_list")).status_code == 200

    def test_income_expense_edit_pages(self, staff_client, income, expense):
        assert staff_client.get(reverse("income_edit", args=[income.id])).status_code == 200
        assert staff_client.get(reverse("expense_edit", args=[expense.id])).status_code == 200

    def test_damage_edit_delete_pages(self, staff_client, damage_report):
        assert staff_client.get(reverse("damage_report_edit", args=[damage_report.id])).status_code == 200
        assert staff_client.get(reverse("damage_report_delete", args=[damage_report.id])).status_code == 200

    def test_floor_plan_edit_delete_pages(self, staff_client, floor_plan):
        assert staff_client.get(reverse("floor_plan_edit", args=[floor_plan.id])).status_code == 200
        assert staff_client.get(reverse("floor_plan_delete", args=[floor_plan.id])).status_code == 200

    def test_timeentry_edit_delete_pages(self, staff_client, timeentry):
        assert staff_client.get(reverse("timeentry_edit", args=[timeentry.id])).status_code == 200
        assert staff_client.get(reverse("timeentry_delete", args=[timeentry.id])).status_code == 200

    def test_rfi_edit_delete_pages(self, staff_client, rfi):
        assert staff_client.get(reverse("rfi_edit", args=[rfi.id])).status_code == 200
        assert staff_client.get(reverse("rfi_delete", args=[rfi.id])).status_code == 200

    def test_issue_edit_delete_pages(self, staff_client, issue):
        assert staff_client.get(reverse("issue_edit", args=[issue.id])).status_code == 200
        assert staff_client.get(reverse("issue_delete", args=[issue.id])).status_code == 200

    def test_risk_edit_delete_pages(self, staff_client, risk):
        assert staff_client.get(reverse("risk_edit", args=[risk.id])).status_code == 200
        assert staff_client.get(reverse("risk_delete", args=[risk.id])).status_code == 200

    def test_unauthenticated_redirects(self, client, floor_plan, damage_report, income, expense, rfi, issue, risk):
        # Unauthenticated should be redirected to login (302)
        assert client.get(reverse("income_list")).status_code in (302, 301)
        assert client.get(reverse("expense_list")).status_code in (302, 301)
        assert client.get(reverse("income_edit", args=[income.id])).status_code in (302, 301)
        assert client.get(reverse("expense_edit", args=[expense.id])).status_code in (302, 301)
        assert client.get(reverse("damage_report_edit", args=[damage_report.id])).status_code in (302, 301)
        assert client.get(reverse("floor_plan_edit", args=[floor_plan.id])).status_code in (302, 301)
        assert client.get(reverse("rfi_edit", args=[rfi.id])).status_code in (302, 301)
        assert client.get(reverse("issue_edit", args=[issue.id])).status_code in (302, 301)
        assert client.get(reverse("risk_edit", args=[risk.id])).status_code in (302, 301)

    # TimeEntry
    # Create a minimal employee/timeentry for redirect check (reuse existing fixtures indirectly)
    # Note: we can't rely on staff-created employee here, so just ensure redirect on pattern
    # We'll skip creating TimeEntry here to avoid auth coupling and validate pattern with a 404 redirect expectation.
