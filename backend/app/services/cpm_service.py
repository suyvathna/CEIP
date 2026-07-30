"""
A deliberately small, from-scratch critical path method (CPM) engine.

Scope, stated plainly: finish-to-start logic only, no lags, no
resource/cost loading, no native P6/MS Project import. That's the
Phase-1 scope from the platform's build plan - a real, defensible
critical-path calculation over hand-entered or spreadsheet-imported
activities, not a full commercial scheduling engine. Phase 2 (a true
Time Impact Analysis with fragnet insertion) reuses the same forward/
backward pass; see analyze_claim_delay below for how it's applied.

The math follows standard CPM: activities and finish-to-start
dependencies form a DAG. A forward pass computes each activity's
earliest start/finish; a backward pass (from the latest finish in the
network) computes latest start/finish; total float is LS - ES, and an
activity is critical when its float is (at most) zero.
"""
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class ActivityInput:
    id: str
    name: str
    planned_start: date
    planned_finish: date


@dataclass
class ActivityCPMResult:
    id: str
    name: str
    duration_days: int
    early_start: date
    early_finish: date
    late_start: date
    late_finish: date
    total_float: int
    is_critical: bool


@dataclass
class CPMResult:
    project_start: date
    project_finish: date
    activities: dict  # id -> ActivityCPMResult


def _topological_order(activity_ids, predecessors: dict):
    """Kahn's algorithm. Raises ValueError on a cycle - a malformed
    programme (e.g. two activities set as each other's predecessor)
    should fail loudly rather than silently produce a wrong critical
    path."""
    successors = defaultdict(list)
    indegree = {a: 0 for a in activity_ids}

    for activity_id, preds in predecessors.items():
        for pred_id in preds:
            successors[pred_id].append(activity_id)
            indegree[activity_id] = indegree.get(activity_id, 0) + 1

    queue = deque([a for a in activity_ids if indegree.get(a, 0) == 0])
    order = []

    while queue:
        current = queue.popleft()
        order.append(current)

        for nxt in successors[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(activity_ids):
        raise ValueError(
            "Programme logic contains a cycle - an activity cannot "
            "(directly or indirectly) be its own predecessor."
        )

    return order, successors


def compute_cpm(
    activities: list[ActivityInput],
    predecessors: dict[str, list[str]],
    duration_overrides: dict[str, int] | None = None,
) -> CPMResult:
    """
    duration_overrides lets a caller extend a specific activity's
    duration (e.g. to model a delay event's impact) without having to
    rebuild ActivityInput objects - see analyze_claim_delay.
    """
    if not activities:
        raise ValueError("Cannot compute a critical path over zero activities.")

    duration_overrides = duration_overrides or {}
    activity_ids = [a.id for a in activities]
    by_id = {a.id: a for a in activities}

    project_start = min(a.planned_start for a in activities)

    duration = {}
    for a in activities:
        base_duration = max((a.planned_finish - a.planned_start).days, 0)
        duration[a.id] = duration_overrides.get(a.id, base_duration)

    order, successors = _topological_order(activity_ids, predecessors)

    early_start = {}
    early_finish = {}

    for activity_id in order:
        preds = predecessors.get(activity_id, [])
        early_start[activity_id] = (
            max(early_finish[p] for p in preds) if preds else 0
        )
        early_finish[activity_id] = early_start[activity_id] + duration[activity_id]

    project_finish_offset = max(early_finish.values())

    late_finish = {}
    late_start = {}

    for activity_id in reversed(order):
        succs = successors.get(activity_id, [])
        late_finish[activity_id] = (
            min(late_start[s] for s in succs) if succs else project_finish_offset
        )
        late_start[activity_id] = late_finish[activity_id] - duration[activity_id]

    results = {}
    for activity_id in activity_ids:
        activity = by_id[activity_id]
        total_float = late_start[activity_id] - early_start[activity_id]

        results[activity_id] = ActivityCPMResult(
            id=activity_id,
            name=activity.name,
            duration_days=duration[activity_id],
            early_start=project_start + timedelta(days=early_start[activity_id]),
            early_finish=project_start + timedelta(days=early_finish[activity_id]),
            late_start=project_start + timedelta(days=late_start[activity_id]),
            late_finish=project_start + timedelta(days=late_finish[activity_id]),
            total_float=total_float,
            is_critical=total_float <= 0,
        )

    return CPMResult(
        project_start=project_start,
        project_finish=project_start + timedelta(days=project_finish_offset),
        activities=results,
    )
