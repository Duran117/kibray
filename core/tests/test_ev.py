from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Project, CostCode, BudgetLine, BudgetProgress


class EarnedValueTests(TestCase):
    def setUp(self):
        # Users
        self.user = User.objects.create_user(username="user", password="x")
        self.staff = User.objects.create_user(username="staff", password="x", is_staff=True)

        # Project and data
        self.project = Project.objects.create(
            name="P1",
            start_date=date.today(),  # requerido por tu modelo
        )
        self.cc = CostCode.objects.create(code="LAB001", name="Labor")
        self.bl = BudgetLine.objects.create(
            project=self.project, cost_code=self.cc,
            description="Labor line", qty=100, unit="hr", unit_cost=10
        )
        self.progress = BudgetProgress.objects.create(
            budget_line=self.bl, date=date.today(), percent_complete=10, qty_completed=10, note="init"
        )

    def test_project_ev_get_ok(self):
        self.client.login(username="user", password="x")
        url = reverse("project_ev", args=[self.project.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Earned Value")

    def test_add_progress_forbidden_for_non_staff(self):
        self.client.login(username="user", password="x")
        url = reverse("project_ev", args=[self.project.id])
        before = BudgetProgress.objects.filter(budget_line__project=self.project).count()
        resp = self.client.post(url, {
            "budget_line": self.bl.id,
            "date": date.today().isoformat(),
            "percent_complete": 20,
            "qty_completed": 20,
            "note": "try add",
        }, follow=False)
        self.assertEqual(resp.status_code, 302)
        after = BudgetProgress.objects.filter(budget_line__project=self.project).count()
        self.assertEqual(before, after)

    def test_add_progress_allowed_for_staff(self):
        self.client.login(username="staff", password="x")
        url = reverse("project_ev", args=[self.project.id])
        before = BudgetProgress.objects.filter(budget_line__project=self.project).count()
        resp = self.client.post(url, {
            "budget_line": self.bl.id,
            "date": date.today().isoformat(),
            "percent_complete": 30,
            "qty_completed": 30,
            "note": "ok",
        })
        self.assertEqual(resp.status_code, 302)
        after = BudgetProgress.objects.filter(budget_line__project=self.project).count()
        self.assertEqual(after, before + 1)

    def test_edit_progress_requires_staff(self):
        self.client.login(username="user", password="x")
        url = reverse("edit_progress", args=[self.project.id, self.progress.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_edit_progress_staff_ok(self):
        self.client.login(username="staff", password="x")
        url = reverse("edit_progress", args=[self.project.id, self.progress.id])
        r1 = self.client.get(url, {"as_of": date.today().isoformat()})
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(url, {
            "date": date.today().isoformat(),
            "percent_complete": 40,
            "qty_completed": 40,
            "note": "upd",
            "as_of": date.today().isoformat(),
        })
        self.assertEqual(r2.status_code, 302)
        self.progress.refresh_from_db()
        self.assertEqual(float(self.progress.percent_complete), 40.0)

    def test_progress_redirect_route(self):
        self.client.login(username="user", password="x")
        url = reverse("project_progress", args=[self.project.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"/projects/{self.project.id}/earned-value/", resp["Location"])

    def test_series_endpoint_json(self):
        self.client.login(username="user", password="x")
        url = reverse("project_ev_series", args=[self.project.id])
        resp = self.client.get(url, {"days": 3, "end": date.today().isoformat()})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("labels", data)
        self.assertIn("PV", data)
        self.assertIn("EV", data)
        self.assertIn("AC", data)