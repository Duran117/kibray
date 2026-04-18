"""
Performance audit — detects N+1 query problems in key views.

Uses Django's CaptureQueriesContext to count SQL queries per view.
Flags views that execute >50 queries (likely N+1 problems).
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def admin_client(db):
    user = User.objects.create_user(
        username="perf_admin",
        email="perf@test.com",
        password="pass1234",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    client.force_login(user)
    return client


# Views to audit — (url_name, kwargs, max_queries)
PERF_TARGETS = [
    ("dashboard", {}, 30),
    ("dashboard_admin", {}, 50),
    ("dashboard_pm", {}, 50),
    ("dashboard_employee", {}, 50),
    ("project_list", {}, 30),
    ("invoice_list", {}, 30),
    ("client_list", {}, 30),
]


@pytest.mark.django_db
@pytest.mark.parametrize("url_name,kwargs,max_queries", PERF_TARGETS)
def test_view_query_count(admin_client, url_name, kwargs, max_queries):
    """Ensure key views don't make excessive queries (N+1 detection)."""
    try:
        url = reverse(url_name, kwargs=kwargs)
    except Exception as e:
        pytest.skip(f"URL '{url_name}' not resolvable: {e}")

    with CaptureQueriesContext(connection) as ctx:
        response = admin_client.get(url)

    assert response.status_code in {200, 302}, (
        f"{url_name} returned {response.status_code}"
    )

    query_count = len(ctx.captured_queries)
    if query_count > max_queries:
        # Print top 5 most common query patterns for diagnosis
        from collections import Counter
        sql_patterns = Counter()
        for q in ctx.captured_queries:
            # Normalize: keep first 80 chars
            sql_patterns[q["sql"][:80]] += 1
        top = sql_patterns.most_common(5)
        diagnosis = "\n".join(f"  {n}x {sql}" for sql, n in top)
        pytest.fail(
            f"{url_name}: {query_count} queries (max {max_queries}).\n"
            f"Top patterns:\n{diagnosis}"
        )
    print(f"  ✅ {url_name}: {query_count} queries")
