"""Smart task selection algorithms for daily planning."""

import re
from datetime import date, datetime
from typing import List, Optional

import aiosqlite


async def select_tasks_for_today(
    db: aiosqlite.Connection, target_date: date, max_tasks: int = 5
) -> dict:
    """Select 3-5 tasks from backlog for today's daily note.

    Uses deterministic algorithm (no LLM) to intelligently choose tasks:
    1. Critical section (1 task max): Deadlines or highest priority
    2. Important section (1-2 tasks): High priority or goal-related
    3. Quick wins section (2-3 tasks): Low effort, high dopamine

    Args:
        db: Database connection
        target_date: Date to select tasks for
        max_tasks: Maximum total tasks to select (default: 5)

    Returns:
        Dict with 'critical', 'important', 'quick_wins' lists and 'backlog_count'
    """
    # Fetch all active todos with metadata
    cursor = await db.execute(
        """
        SELECT id, title, priority, notes, time_estimate, skipped_count,
               last_scheduled, created_at
        FROM todos
        WHERE status = 'active'
        ORDER BY created_at ASC
        """
    )
    all_todos = await cursor.fetchall()

    if not all_todos:
        return {
            "critical": [],
            "important": [],
            "quick_wins": [],
            "backlog_count": 0,
        }

    # Convert to dicts for easier handling
    todos = [dict(row) for row in all_todos]

    # Filter out tasks stuck in backlog hell (moved 5+ times)
    todos = [t for t in todos if (t["skipped_count"] or 0) < 5]

    # Categorize todos
    critical = await _select_critical_tasks(todos, target_date)
    important = await _select_important_tasks(todos, critical, max_important=2)
    quick_wins = await _select_quick_wins(todos, critical + important, max_quick=3)

    # Limit total tasks
    selected_tasks = critical + important + quick_wins
    if len(selected_tasks) > max_tasks:
        # Prioritize: keep all critical, trim quick wins first, then important
        quick_wins = quick_wins[: max(0, max_tasks - len(critical) - len(important))]
        if len(critical) + len(important) > max_tasks:
            important = important[: max(0, max_tasks - len(critical))]

    # Update last_scheduled for selected tasks
    selected_ids = [t["id"] for t in critical + important + quick_wins]
    if selected_ids:
        placeholders = ",".join("?" * len(selected_ids))
        await db.execute(
            f"UPDATE todos SET last_scheduled = ? WHERE id IN ({placeholders})",
            [target_date.isoformat()] + selected_ids,
        )
        await db.commit()

    return {
        "critical": critical,
        "important": important,
        "quick_wins": quick_wins,
        "backlog_count": len(all_todos),
    }


async def _select_critical_tasks(todos: List[dict], target_date: date) -> List[dict]:
    """Select 0-1 critical task with deadline or highest priority.

    Priority:
    1. Tasks with today's date mentioned in notes (deadlines)
    2. High priority tasks that haven't been skipped too many times
    """
    # Look for deadline mentions
    date_patterns = [
        target_date.strftime("%Y-%m-%d"),  # 2025-11-07
        target_date.strftime("%m/%d"),  # 11/07
        target_date.strftime("%B %d"),  # November 07
        target_date.strftime("%b %d"),  # Nov 07
    ]

    for todo in todos:
        notes = todo.get("notes") or ""
        if any(pattern in notes for pattern in date_patterns):
            return [todo]

    # Check for [Deadline] flag
    for todo in todos:
        notes = todo.get("notes") or ""
        if "[Deadline]" in notes:
            return [todo]

    # Fall back to highest priority that's not too stale
    high_priority = [t for t in todos if t["priority"] == "high"]
    high_priority.sort(key=lambda t: t.get("skipped_count", 0))

    if high_priority:
        return [high_priority[0]]

    return []


async def _select_important_tasks(
    todos: List[dict], exclude: List[dict], max_important: int = 2
) -> List[dict]:
    """Select 1-2 important high-impact tasks.

    Priority:
    1. High priority tasks
    2. Tasks with [Sprint Work] or [Management] tags
    3. Medium priority tasks, oldest first
    """
    exclude_ids = {t["id"] for t in exclude}
    available = [t for t in todos if t["id"] not in exclude_ids]

    important = []

    # High priority tasks
    high_priority = [t for t in available if t["priority"] == "high"]
    high_priority.sort(key=lambda t: t.get("skipped_count", 0))
    important.extend(high_priority[:max_important])

    if len(important) >= max_important:
        return important[:max_important]

    # Sprint/Management work
    exclude_ids.update(t["id"] for t in important)
    available = [t for t in available if t["id"] not in exclude_ids]

    sprint_tasks = [
        t
        for t in available
        if any(
            tag in (t.get("notes") or "")
            for tag in ["[Sprint Work]", "[Management]"]
        )
    ]
    important.extend(sprint_tasks[: max_important - len(important)])

    if len(important) >= max_important:
        return important[:max_important]

    # Medium priority, oldest first
    exclude_ids.update(t["id"] for t in important)
    available = [t for t in available if t["id"] not in exclude_ids]

    medium_priority = [t for t in available if t["priority"] == "medium"]
    medium_priority.sort(key=lambda t: t["created_at"])
    important.extend(medium_priority[: max_important - len(important)])

    return important[:max_important]


async def _select_quick_wins(
    todos: List[dict], exclude: List[dict], max_quick: int = 3
) -> List[dict]:
    """Select 2-3 quick win tasks for dopamine hits.

    Priority:
    1. Tasks marked as [Quick Win]
    2. Tasks with time_estimate <= 30 minutes
    3. Low priority tasks (often easier)
    """
    exclude_ids = {t["id"] for t in exclude}
    available = [t for t in todos if t["id"] not in exclude_ids]

    quick_wins = []

    # Explicit quick wins
    explicit_quick = [
        t for t in available if "[Quick Win]" in (t.get("notes") or "")
    ]
    quick_wins.extend(explicit_quick[:max_quick])

    if len(quick_wins) >= max_quick:
        return quick_wins[:max_quick]

    # Time estimate based
    exclude_ids.update(t["id"] for t in quick_wins)
    available = [t for t in available if t["id"] not in exclude_ids]

    time_based = [
        t for t in available if t.get("time_estimate") and t["time_estimate"] <= 30
    ]
    time_based.sort(key=lambda t: t["time_estimate"])
    quick_wins.extend(time_based[: max_quick - len(quick_wins)])

    if len(quick_wins) >= max_quick:
        return quick_wins[:max_quick]

    # Low priority tasks
    exclude_ids.update(t["id"] for t in quick_wins)
    available = [t for t in available if t["id"] not in exclude_ids]

    low_priority = [t for t in available if t["priority"] == "low"]
    low_priority.sort(key=lambda t: t["created_at"])
    quick_wins.extend(low_priority[: max_quick - len(quick_wins)])

    return quick_wins[:max_quick]


async def increment_skip_counts(
    db: aiosqlite.Connection, task_ids: List[int]
) -> None:
    """Increment skip count for tasks that weren't scheduled today.

    This tracks tasks stuck in "backlog hell" - moved forward repeatedly.
    """
    if not task_ids:
        return

    placeholders = ",".join("?" * len(task_ids))
    await db.execute(
        f"""
        UPDATE todos
        SET skipped_count = COALESCE(skipped_count, 0) + 1
        WHERE id IN ({placeholders}) AND status = 'active'
        """,
        task_ids,
    )
    await db.commit()
