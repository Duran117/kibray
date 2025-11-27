"""
Performance regression tests for API endpoints.
Ensures critical queries use prefetch_related/select_related to avoid N+1.
"""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext

from core.models import Expense, Project

pytestmark = pytest.mark.django_db


def test_project_budget_overview_query_count(client):
    """Ensure budget_overview uses prefetch to avoid N+1 queries"""
    User = get_user_model()
    user = User.objects.create_user(username="perfuser", password="pass123")
    client.force_login(user)

    # Create 10 projects with expenses
    for i in range(10):
        proj = Project.objects.create(name=f"Project {i}", start_date=date.today(), budget_total=10000)
        for j in range(3):
            Expense.objects.create(
                project=proj,
                project_name=f"Project {i}",
                amount=100 * (j + 1),
                date=date.today(),
                category="MATERIALES",
            )

    with CaptureQueriesContext(connection) as ctx:
        resp = client.get("/api/v1/projects/budget_overview/")
        assert resp.status_code == 200

    # With prefetch_related('expenses'), expect base query + 1 prefetch
    # Without it, would be 1 (projects) + 10 (aggregate per project) = 11+
    # Target: <= 3 queries (1 for projects, 1 for prefetch, 1 for auth/session)
    query_count = len(ctx.captured_queries)
    assert query_count <= 5, f"Too many queries ({query_count}); expected <=5 with prefetch_related"


def test_invoice_list_query_count(client):
    """Ensure invoice list uses select_related to reduce queries"""
    User = get_user_model()
    user = User.objects.create_user(username="invuser", password="pass123")
    client.force_login(user)

    from core.models import Invoice

    # Create invoices with projects
    for i in range(5):
        proj = Project.objects.create(name=f"Inv Project {i}", start_date=date.today())
        Invoice.objects.create(project=proj, invoice_number=f"INV-{i}", date_issued=date.today(), total_amount=1000)

    with CaptureQueriesContext(connection) as ctx:
        resp = client.get("/api/v1/invoices/")
        assert resp.status_code == 200

    query_count = len(ctx.captured_queries)
    # Should be: 1 auth/session, 1 invoice query with select_related, 1 prefetch lines/payments
    assert query_count <= 6, f"Too many queries ({query_count}); expected <=6 with select_related/prefetch"
