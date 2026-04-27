"""Critical Path Method (CPM) service for project tasks.

Phase D2 — pure-additive implementation that runs forward/backward passes over
the existing ``TaskDependency`` graph and reports earliest/latest schedules,
slack and the critical chain for a project.

Design notes
------------
The algorithm is deliberately decoupled from persistence:

* ``compute_critical_path`` is the public entry point. It loads tasks and
  dependencies for a project but delegates the actual math to
  ``run_cpm`` which operates on plain Python data and is therefore trivial to
  unit-test with synthetic graphs.
* Durations can be injected via the ``durations`` argument. When omitted, the
  default resolver inspects each ``Task`` (tracked seconds, ``started_at`` /
  ``completed_at`` window, then a fallback). This keeps the service usable in
  production today while remaining stable in tests.
* All time math is in **minutes** to align with ``TaskDependency.lag_minutes``.

Dependency semantics (with lag ``L`` and ``s = successor`` / ``p = predecessor``):

* ``FS`` (Finish-to-Start, default): ``ES(s) >= EF(p) + L``
* ``SS`` (Start-to-Start):           ``ES(s) >= ES(p) + L``
* ``FF`` (Finish-to-Finish):         ``EF(s) >= EF(p) + L``  ⇒  ``ES(s) >= EF(p) + L - dur(s)``
* ``SF`` (Start-to-Finish):          ``EF(s) >= ES(p) + L``  ⇒  ``ES(s) >= ES(p) + L - dur(s)``

Backward pass mirrors these constraints to produce ``LF`` and ``LS``.
Slack is ``LS - ES`` (equivalently ``LF - EF``); a task is critical when its
slack equals zero **and** it lies on a chain that reaches the project finish.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Sequence

DEFAULT_TASK_DURATION_MINUTES = 480  # one 8-hour work-day fallback


class CriticalPathError(Exception):
    """Base error raised by the CPM service."""


class CriticalPathCycleError(CriticalPathError):
    """Raised when the dependency graph still contains a cycle.

    ``TaskDependency.clean()`` should already prevent this at write time, so
    hitting it indicates data was inserted bypassing validation.
    """


@dataclass(frozen=True)
class CPMEdge:
    predecessor: int
    successor: int
    type: str = "FS"
    lag_minutes: int = 0


@dataclass
class CPMNode:
    task_id: int
    duration_minutes: int
    es: int = 0
    ef: int = 0
    ls: int = 0
    lf: int = 0
    slack_minutes: int = 0
    is_critical: bool = False
    title: str = ""
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pure algorithm (no Django dependency)
# ---------------------------------------------------------------------------


def _topological_order(node_ids: Sequence[int], edges: Sequence[CPMEdge]) -> list[int]:
    indeg: dict[int, int] = {nid: 0 for nid in node_ids}
    succ: dict[int, list[int]] = defaultdict(list)
    for e in edges:
        # Only count edges where both endpoints are in scope.
        if e.predecessor in indeg and e.successor in indeg:
            indeg[e.successor] += 1
            succ[e.predecessor].append(e.successor)

    queue: deque[int] = deque(nid for nid, d in indeg.items() if d == 0)
    order: list[int] = []
    while queue:
        nid = queue.popleft()
        order.append(nid)
        for nxt in succ[nid]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(node_ids):
        remaining = [nid for nid in node_ids if nid not in set(order)]
        raise CriticalPathCycleError(
            f"Cycle detected in dependency graph among tasks: {sorted(remaining)}"
        )
    return order


def run_cpm(
    durations: Mapping[int, int],
    edges: Iterable[CPMEdge],
    *,
    titles: Mapping[int, str] | None = None,
) -> dict:
    """Run forward + backward passes over a graph of tasks.

    Parameters
    ----------
    durations:
        ``{task_id: duration_minutes}``. ``0`` is allowed (milestone).
    edges:
        Iterable of :class:`CPMEdge`. Edges referring to tasks not present in
        ``durations`` are ignored.
    titles:
        Optional ``{task_id: title}`` for nicer output.
    """
    titles = titles or {}
    node_ids = list(durations.keys())
    edges = [e for e in edges if e.predecessor in durations and e.successor in durations]

    nodes: dict[int, CPMNode] = {
        nid: CPMNode(
            task_id=nid,
            duration_minutes=max(0, int(durations[nid])),
            title=titles.get(nid, ""),
        )
        for nid in node_ids
    }

    if not nodes:
        return {
            "tasks": [],
            "edges": [],
            "critical_path_ids": [],
            "project_duration_minutes": 0,
        }

    incoming: dict[int, list[CPMEdge]] = defaultdict(list)
    outgoing: dict[int, list[CPMEdge]] = defaultdict(list)
    for e in edges:
        incoming[e.successor].append(e)
        outgoing[e.predecessor].append(e)

    order = _topological_order(node_ids, edges)

    # ----- Forward pass: ES / EF -----
    for nid in order:
        node = nodes[nid]
        candidates = [0]
        for e in incoming[nid]:
            p = nodes[e.predecessor]
            t = e.type
            if t == "FS":
                candidates.append(p.ef + e.lag_minutes)
            elif t == "SS":
                candidates.append(p.es + e.lag_minutes)
            elif t == "FF":
                candidates.append(p.ef + e.lag_minutes - node.duration_minutes)
            elif t == "SF":
                candidates.append(p.es + e.lag_minutes - node.duration_minutes)
            else:  # unknown type defaults to FS
                candidates.append(p.ef + e.lag_minutes)
        node.es = max(candidates)
        node.ef = node.es + node.duration_minutes

    project_finish = max(n.ef for n in nodes.values())

    # ----- Backward pass: LS / LF -----
    # Initialise: nodes without successors anchor to project_finish.
    for nid in order:
        if not outgoing[nid]:
            nodes[nid].lf = project_finish
            nodes[nid].ls = project_finish - nodes[nid].duration_minutes

    for nid in reversed(order):
        node = nodes[nid]
        if not outgoing[nid]:
            continue  # already initialised
        candidates = []
        for e in outgoing[nid]:
            s = nodes[e.successor]
            t = e.type
            if t == "FS":
                candidates.append(s.ls - e.lag_minutes)
            elif t == "SS":
                candidates.append(s.ls - e.lag_minutes + node.duration_minutes)
            elif t == "FF":
                candidates.append(s.lf - e.lag_minutes)
            elif t == "SF":
                candidates.append(s.lf - e.lag_minutes + node.duration_minutes)
            else:
                candidates.append(s.ls - e.lag_minutes)
        node.lf = min(candidates) if candidates else project_finish
        node.ls = node.lf - node.duration_minutes

    # ----- Slack + critical flag -----
    for n in nodes.values():
        n.slack_minutes = n.ls - n.es
        n.is_critical = n.slack_minutes == 0

    # ----- Critical path chain (for display) -----
    # Pick a starting critical node with no critical predecessors, then walk
    # forward through critical successors choosing the one whose ES matches
    # the constraint imposed by the edge. This produces a deterministic chain
    # even if multiple critical paths exist.
    critical_ids: list[int] = []
    visited: set[int] = set()
    crit_nodes = [n for n in nodes.values() if n.is_critical]
    if crit_nodes:
        crit_set = {n.task_id for n in crit_nodes}

        def has_critical_predecessor(nid: int) -> bool:
            return any(e.predecessor in crit_set for e in incoming[nid])

        # Start: critical node without a critical predecessor; pick the one
        # with smallest ES (then id) for determinism.
        starts = sorted(
            [n for n in crit_nodes if not has_critical_predecessor(n.task_id)],
            key=lambda n: (n.es, n.task_id),
        )
        if starts:
            current = starts[0]
            while current and current.task_id not in visited:
                visited.add(current.task_id)
                critical_ids.append(current.task_id)
                # find next critical successor
                next_candidates = [
                    nodes[e.successor]
                    for e in outgoing[current.task_id]
                    if e.successor in crit_set and nodes[e.successor].task_id not in visited
                ]
                next_candidates.sort(key=lambda n: (n.es, n.task_id))
                current = next_candidates[0] if next_candidates else None

    return {
        "tasks": [
            {
                "task_id": n.task_id,
                "title": n.title,
                "duration_minutes": n.duration_minutes,
                "es": n.es,
                "ef": n.ef,
                "ls": n.ls,
                "lf": n.lf,
                "slack_minutes": n.slack_minutes,
                "is_critical": n.is_critical,
            }
            for n in sorted(nodes.values(), key=lambda x: (x.es, x.task_id))
        ],
        "edges": [
            {
                "predecessor": e.predecessor,
                "successor": e.successor,
                "type": e.type,
                "lag_minutes": e.lag_minutes,
            }
            for e in edges
        ],
        "critical_path_ids": critical_ids,
        "project_duration_minutes": project_finish,
    }


# ---------------------------------------------------------------------------
# Django integration layer
# ---------------------------------------------------------------------------


def _default_duration_resolver(task) -> int:
    """Best-effort duration in minutes for a Task instance.

    Order of preference:
    1. ``time_tracked_seconds`` if > 0 (real measured work).
    2. ``started_at`` / ``completed_at`` window if both present.
    3. ``DEFAULT_TASK_DURATION_MINUTES`` fallback.
    """
    tracked = getattr(task, "time_tracked_seconds", 0) or 0
    if tracked > 0:
        return max(1, tracked // 60)

    started = getattr(task, "started_at", None)
    completed = getattr(task, "completed_at", None)
    if started and completed and completed > started:
        return max(1, int((completed - started).total_seconds() // 60))

    return DEFAULT_TASK_DURATION_MINUTES


def compute_critical_path(
    project_id: int,
    *,
    durations: Mapping[int, int] | None = None,
    duration_resolver: Callable | None = None,
) -> dict:
    """Compute the CPM result for a single project.

    Parameters
    ----------
    project_id:
        ``Project.id`` whose tasks/dependencies will be analysed.
    durations:
        Optional explicit per-task overrides ``{task_id: minutes}``. Tasks not
        present in this mapping fall back to ``duration_resolver``.
    duration_resolver:
        Optional callable ``resolver(task) -> int`` (minutes). Defaults to
        :func:`_default_duration_resolver`.

    Returns
    -------
    dict
        See :func:`run_cpm` for the schema. The dict additionally includes
        ``project_id``.
    """
    from core.models import Task, TaskDependency  # local import: avoid cycle at import time

    resolver = duration_resolver or _default_duration_resolver
    overrides = dict(durations or {})

    tasks = list(
        Task.objects.filter(project_id=project_id).only(
            "id", "title", "time_tracked_seconds", "started_at", "completed_at"
        )
    )
    task_ids = {t.id for t in tasks}
    titles = {t.id: t.title for t in tasks}

    durations_map: dict[int, int] = {}
    for t in tasks:
        if t.id in overrides:
            durations_map[t.id] = max(0, int(overrides[t.id]))
        else:
            durations_map[t.id] = max(0, int(resolver(t)))

    deps = TaskDependency.objects.filter(
        task_id__in=task_ids, predecessor_id__in=task_ids
    ).values("task_id", "predecessor_id", "type", "lag_minutes")

    edges = [
        CPMEdge(
            predecessor=d["predecessor_id"],
            successor=d["task_id"],
            type=d["type"] or "FS",
            lag_minutes=int(d["lag_minutes"] or 0),
        )
        for d in deps
    ]

    result = run_cpm(durations_map, edges, titles=titles)
    result["project_id"] = project_id
    return result


__all__ = [
    "CPMEdge",
    "CPMNode",
    "CriticalPathError",
    "CriticalPathCycleError",
    "DEFAULT_TASK_DURATION_MINUTES",
    "compute_critical_path",
    "run_cpm",
]
