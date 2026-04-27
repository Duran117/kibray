"""Tests for the Critical Path Method (CPM) service — Phase D2.

Covers:
* Pure algorithm (``run_cpm``) with synthetic graphs — linear, parallel,
  diamond, all four dependency types, lag handling, milestones, isolated nodes.
* Cycle detection — ``CriticalPathCycleError`` is raised when topological sort
  cannot complete.
* Django integration (``compute_critical_path``) — pulls Tasks +
  TaskDependency for a project, applies overrides, falls back to the default
  resolver.
* REST endpoint ``GET /api/v1/projects/{id}/critical-path/`` with query-string
  duration overrides.
"""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Project, Task, TaskDependency
from core.services.critical_path import (
    CPMEdge,
    CriticalPathCycleError,
    DEFAULT_TASK_DURATION_MINUTES,
    compute_critical_path,
    run_cpm,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Pure algorithm
# ---------------------------------------------------------------------------


class TestRunCPMLinear:
    def test_empty_graph_returns_zero_duration(self):
        result = run_cpm({}, [])
        assert result["tasks"] == []
        assert result["edges"] == []
        assert result["critical_path_ids"] == []
        assert result["project_duration_minutes"] == 0

    def test_single_task(self):
        result = run_cpm({1: 60}, [])
        assert result["project_duration_minutes"] == 60
        t = result["tasks"][0]
        assert t["es"] == 0 and t["ef"] == 60
        assert t["ls"] == 0 and t["lf"] == 60
        assert t["slack_minutes"] == 0
        assert t["is_critical"] is True
        assert result["critical_path_ids"] == [1]

    def test_linear_chain_FS(self):
        # 1 -> 2 -> 3, durations 10 / 20 / 30 → total 60
        edges = [
            CPMEdge(predecessor=1, successor=2, type="FS"),
            CPMEdge(predecessor=2, successor=3, type="FS"),
        ]
        r = run_cpm({1: 10, 2: 20, 3: 30}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        assert nodes[1]["es"] == 0 and nodes[1]["ef"] == 10
        assert nodes[2]["es"] == 10 and nodes[2]["ef"] == 30
        assert nodes[3]["es"] == 30 and nodes[3]["ef"] == 60
        assert r["project_duration_minutes"] == 60
        for n in nodes.values():
            assert n["slack_minutes"] == 0
        assert r["critical_path_ids"] == [1, 2, 3]


class TestRunCPMParallelAndDiamond:
    def test_parallel_branches_pick_longer_as_critical(self):
        # 1 -> 2 (long) and 1 -> 3 (short); 2 and 3 -> 4
        edges = [
            CPMEdge(1, 2, "FS"),
            CPMEdge(1, 3, "FS"),
            CPMEdge(2, 4, "FS"),
            CPMEdge(3, 4, "FS"),
        ]
        r = run_cpm({1: 10, 2: 50, 3: 20, 4: 5}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        assert r["project_duration_minutes"] == 65  # 10 + 50 + 5
        assert nodes[2]["is_critical"] is True
        assert nodes[3]["is_critical"] is False
        assert nodes[3]["slack_minutes"] == 30  # 50 - 20
        assert r["critical_path_ids"] == [1, 2, 4]

    def test_diamond_with_equal_branches_all_critical(self):
        edges = [CPMEdge(1, 2), CPMEdge(1, 3), CPMEdge(2, 4), CPMEdge(3, 4)]
        r = run_cpm({1: 5, 2: 10, 3: 10, 4: 5}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        assert r["project_duration_minutes"] == 20
        assert all(nodes[i]["is_critical"] for i in (1, 2, 3, 4))
        # Critical chain is deterministic: smallest task_id wins on ties.
        assert r["critical_path_ids"] == [1, 2, 4]

    def test_isolated_node_takes_zero_offset(self):
        # Two disjoint tasks, neither has predecessors
        r = run_cpm({1: 30, 2: 50}, [])
        nodes = {t["task_id"]: t for t in r["tasks"]}
        assert nodes[1]["es"] == 0 and nodes[2]["es"] == 0
        assert r["project_duration_minutes"] == 50
        # Only 2 is critical (drives finish); 1 has slack of 20
        assert nodes[2]["is_critical"] is True
        assert nodes[1]["is_critical"] is False
        assert nodes[1]["slack_minutes"] == 20


class TestRunCPMDependencyTypes:
    def test_FS_with_lag(self):
        edges = [CPMEdge(1, 2, "FS", lag_minutes=15)]
        r = run_cpm({1: 10, 2: 20}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        assert nodes[2]["es"] == 25  # EF(1)=10 + lag 15
        assert nodes[2]["ef"] == 45
        assert r["project_duration_minutes"] == 45

    def test_SS_with_lag(self):
        # Successor can start 5 min after predecessor starts.
        edges = [CPMEdge(1, 2, "SS", lag_minutes=5)]
        r = run_cpm({1: 60, 2: 40}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        assert nodes[2]["es"] == 5
        assert nodes[2]["ef"] == 45
        # Project finish = max(EF) = max(60, 45) = 60
        assert r["project_duration_minutes"] == 60

    def test_FF_constraint(self):
        # Successor must finish at or after EF(pred) + lag.
        edges = [CPMEdge(1, 2, "FF", lag_minutes=10)]
        r = run_cpm({1: 30, 2: 5}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        # ES(2) = EF(1) + lag - dur(2) = 30 + 10 - 5 = 35
        assert nodes[2]["es"] == 35
        assert nodes[2]["ef"] == 40

    def test_SF_constraint(self):
        edges = [CPMEdge(1, 2, "SF", lag_minutes=20)]
        r = run_cpm({1: 30, 2: 5}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        # ES(2) = ES(1) + lag - dur(2) = 0 + 20 - 5 = 15
        assert nodes[2]["es"] == 15
        assert nodes[2]["ef"] == 20

    def test_zero_duration_milestone(self):
        # Milestone (duration 0) between two real tasks
        edges = [CPMEdge(1, 2, "FS"), CPMEdge(2, 3, "FS")]
        r = run_cpm({1: 10, 2: 0, 3: 20}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        assert nodes[2]["es"] == nodes[2]["ef"] == 10
        assert nodes[3]["es"] == 10 and nodes[3]["ef"] == 30
        assert r["project_duration_minutes"] == 30
        assert nodes[2]["is_critical"] is True


class TestRunCPMSlack:
    def test_non_critical_slack_correct(self):
        # 1 -> 2 (critical, 30), 1 -> 3 (slack), 2 & 3 -> 4
        edges = [CPMEdge(1, 2), CPMEdge(1, 3), CPMEdge(2, 4), CPMEdge(3, 4)]
        r = run_cpm({1: 10, 2: 30, 3: 10, 4: 5}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        # Project finish: 10 + 30 + 5 = 45
        # Task 3: ES=10, EF=20, LF must equal LS(4)=40 → so LS(3)=40-10=30, LF(3)=40
        assert nodes[3]["slack_minutes"] == 20
        assert nodes[3]["is_critical"] is False
        # Critical: 1, 2, 4
        for tid in (1, 2, 4):
            assert nodes[tid]["is_critical"] is True


class TestRunCPMCycle:
    def test_cycle_raises(self):
        edges = [CPMEdge(1, 2), CPMEdge(2, 3), CPMEdge(3, 1)]
        with pytest.raises(CriticalPathCycleError):
            run_cpm({1: 10, 2: 10, 3: 10}, edges)

    def test_self_loop_raises(self):
        with pytest.raises(CriticalPathCycleError):
            run_cpm({1: 10}, [CPMEdge(1, 1)])


class TestRunCPMEdgeFiltering:
    def test_edges_referencing_unknown_nodes_ignored(self):
        # Edge 99->1 should be ignored because 99 isn't in durations.
        edges = [CPMEdge(99, 1), CPMEdge(1, 2)]
        r = run_cpm({1: 10, 2: 5}, edges)
        nodes = {t["task_id"]: t for t in r["tasks"]}
        assert nodes[1]["es"] == 0
        assert nodes[2]["es"] == 10
        assert r["project_duration_minutes"] == 15


# ---------------------------------------------------------------------------
# Django integration
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="cpm_admin", password="pass", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="CPM Project",
        client="Client",
        start_date=date.today(),
        address="Addr",
    )


@pytest.fixture
def chain_tasks(db, project, admin_user):
    a = Task.objects.create(project=project, title="A", status="Pending", created_by=admin_user)
    b = Task.objects.create(project=project, title="B", status="Pending", created_by=admin_user)
    c = Task.objects.create(project=project, title="C", status="Pending", created_by=admin_user)
    TaskDependency.objects.create(task=b, predecessor=a, type="FS")
    TaskDependency.objects.create(task=c, predecessor=b, type="FS")
    return a, b, c


class TestComputeCriticalPathDjango:
    def test_default_durations_fallback(self, chain_tasks):
        a, b, c = chain_tasks
        result = compute_critical_path(a.project_id)
        assert result["project_id"] == a.project_id
        assert {t["task_id"] for t in result["tasks"]} == {a.id, b.id, c.id}
        # All three default to DEFAULT_TASK_DURATION_MINUTES
        for t in result["tasks"]:
            assert t["duration_minutes"] == DEFAULT_TASK_DURATION_MINUTES
        assert result["project_duration_minutes"] == 3 * DEFAULT_TASK_DURATION_MINUTES
        assert result["critical_path_ids"] == [a.id, b.id, c.id]

    def test_explicit_overrides(self, chain_tasks):
        a, b, c = chain_tasks
        overrides = {a.id: 30, b.id: 60, c.id: 10}
        result = compute_critical_path(a.project_id, durations=overrides)
        nodes = {t["task_id"]: t for t in result["tasks"]}
        assert nodes[a.id]["duration_minutes"] == 30
        assert nodes[b.id]["duration_minutes"] == 60
        assert nodes[c.id]["duration_minutes"] == 10
        assert result["project_duration_minutes"] == 100

    def test_uses_tracked_seconds_when_available(self, project, admin_user):
        a = Task.objects.create(
            project=project,
            title="tracked",
            status="Completed",
            time_tracked_seconds=3600,  # 60 minutes
            created_by=admin_user,
        )
        result = compute_critical_path(project.id)
        nodes = {t["task_id"]: t for t in result["tasks"]}
        assert nodes[a.id]["duration_minutes"] == 60

    def test_other_project_tasks_excluded(self, chain_tasks, admin_user):
        a, b, c = chain_tasks
        other = Project.objects.create(
            name="Other", client="X", start_date=date.today(), address="addr"
        )
        Task.objects.create(project=other, title="ZZ", created_by=admin_user)
        result = compute_critical_path(a.project_id)
        ids = {t["task_id"] for t in result["tasks"]}
        assert ids == {a.id, b.id, c.id}

    def test_isolated_task_with_no_deps(self, project, admin_user):
        Task.objects.create(project=project, title="solo", created_by=admin_user)
        result = compute_critical_path(project.id)
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["is_critical"] is True


# ---------------------------------------------------------------------------
# REST endpoint
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


class TestCriticalPathEndpoint:
    def test_endpoint_returns_payload(self, api_client, admin_user, chain_tasks):
        a, b, c = chain_tasks
        api_client.force_authenticate(user=admin_user)
        url = f"/api/v1/projects/{a.project_id}/critical-path/"
        res = api_client.get(url)
        assert res.status_code == 200, res.data
        body = res.data
        assert body["project_id"] == a.project_id
        assert {t["task_id"] for t in body["tasks"]} == {a.id, b.id, c.id}
        assert body["critical_path_ids"] == [a.id, b.id, c.id]

    def test_endpoint_accepts_duration_overrides(self, api_client, admin_user, chain_tasks):
        a, b, c = chain_tasks
        api_client.force_authenticate(user=admin_user)
        url = (
            f"/api/v1/projects/{a.project_id}/critical-path/"
            f"?durations={a.id}:30,{b.id}:60,{c.id}:10"
        )
        res = api_client.get(url)
        assert res.status_code == 200
        assert res.data["project_duration_minutes"] == 100

    def test_endpoint_requires_authentication(self, api_client, chain_tasks):
        a, _, _ = chain_tasks
        url = f"/api/v1/projects/{a.project_id}/critical-path/"
        res = api_client.get(url)
        assert res.status_code in (401, 403)
