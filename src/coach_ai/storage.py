"""Database storage layer for Coach AI."""

import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

import aiosqlite

from coach_ai.migrations import migrate_database


# Global database connection
_db: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    """Get or create database connection."""
    global _db

    if _db is None:
        # Determine database path
        db_path = os.environ.get("COACH_DB_PATH", "data/coach.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        _db = await aiosqlite.connect(db_path)
        _db.row_factory = aiosqlite.Row

        # Initialize schema
        await _db.executescript(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                notes TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                timeframe TEXT,
                category TEXT DEFAULT 'general',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS accomplishments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await _db.commit()

        # Run migrations
        await migrate_database(_db)

    return _db


# ============================================================================
# TODO OPERATIONS
# ============================================================================


async def add_todo(
    title: str, priority: str = "medium", notes: str = "", quick: bool = False
) -> str:
    """Add a new todo item with smart categorization.

    Args:
        title: The todo title/description
        priority: Priority level - 'low', 'medium', or 'high' (default: 'medium')
        notes: Optional additional notes or context
        quick: Mark as quick win (automatically sets low priority and time estimate)

    Returns:
        Success message with task ID
    """
    db = await get_db()

    # Validate priority
    if priority not in ["low", "medium", "high"]:
        priority = "medium"

    # Auto-categorization based on keywords
    auto_notes = []
    title_lower = title.lower()
    notes_lower = notes.lower()

    # Category detection
    if any(keyword in title_lower for keyword in ["sprint", "sidecar", "migration"]):
        auto_notes.append("[Sprint Work]")
    if any(keyword in title_lower for keyword in ["korosh", "manager", "presentation", "meeting"]):
        auto_notes.append("[Management]")
    if any(keyword in title_lower or keyword in notes_lower for keyword in ["deadline", "due"]):
        auto_notes.append("[Deadline]")

    # Quick win handling
    time_estimate = None
    if quick or any(keyword in title_lower or keyword in notes_lower for keyword in ["quick", "easy"]):
        priority = "low"  # Quick wins are low priority for selection
        auto_notes.append("[Quick Win]")
        time_estimate = 15  # Default 15 minutes for quick wins

    # Extract time estimates from notes (e.g., "30min", "2h", "1hr")
    time_pattern = r"(\d+)\s*(min|mins|minute|minutes|h|hr|hrs|hour|hours)"
    time_match = re.search(time_pattern, notes_lower)
    if time_match and not time_estimate:
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        if unit.startswith("h"):
            time_estimate = amount * 60
        else:
            time_estimate = amount

        # Mark as quick win if under 30 minutes
        if time_estimate <= 30 and "[Quick Win]" not in auto_notes:
            auto_notes.append("[Quick Win]")

    # Combine notes
    enhanced_notes = notes
    if auto_notes:
        prefix = " ".join(auto_notes)
        enhanced_notes = f"{prefix}\n{notes}" if notes else prefix

    # Insert todo
    await db.execute(
        "INSERT INTO todos (title, priority, notes, time_estimate) VALUES (?, ?, ?, ?)",
        (title, priority, enhanced_notes, time_estimate),
    )
    await db.commit()

    # Get the ID of inserted todo
    cursor = await db.execute("SELECT last_insert_rowid()")
    row = await cursor.fetchone()
    todo_id = row[0]

    result = f"✓ Added todo #{todo_id}: {title}"
    if quick or "[Quick Win]" in auto_notes:
        result += " (quick win)"
    result += f"\n  Priority: {priority}"
    if time_estimate:
        result += f" | Estimated time: {time_estimate}min"
    result += "\n  It's in your backlog - run 'start_my_day' tomorrow to schedule it."

    return result


async def list_todos(status: str = "active") -> str:
    """List todos filtered by status.

    Args:
        status: Filter by 'active', 'completed', or 'all'

    Returns:
        Formatted list of todos
    """
    db = await get_db()

    if status == "all":
        cursor = await db.execute(
            "SELECT * FROM todos ORDER BY priority DESC, created_at DESC"
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM todos WHERE status = ? ORDER BY priority DESC, created_at DESC",
            (status,),
        )

    rows = await cursor.fetchall()

    if not rows:
        return f"No {status} todos found."

    # Format output
    result = f"\n=== {status.upper()} TODOS ===\n\n"

    # Group by priority
    priority_groups = {"high": [], "medium": [], "low": []}
    for row in rows:
        priority_groups[row["priority"]].append(row)

    for priority in ["high", "medium", "low"]:
        todos = priority_groups[priority]
        if todos:
            result += f"{priority.upper()} PRIORITY:\n"
            for todo in todos:
                result += f"  [{todo['id']}] {todo['title']}\n"
                if todo["notes"]:
                    result += f"      Notes: {todo['notes']}\n"
            result += "\n"

    return result.strip()


async def complete_todo(todo_id: int) -> str:
    """Mark a todo as complete.

    Args:
        todo_id: The ID of the todo to complete

    Returns:
        Success message or error
    """
    db = await get_db()

    # Get todo title for confirmation
    cursor = await db.execute("SELECT title FROM todos WHERE id = ?", (todo_id,))
    row = await cursor.fetchone()

    if not row:
        return f"Error: Todo #{todo_id} not found."

    # Mark as complete
    await db.execute(
        "UPDATE todos SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (todo_id,),
    )
    await db.commit()

    return f"✓ Completed: {row['title']}"


async def delete_todo(todo_id: int) -> str:
    """Delete a todo permanently.

    Args:
        todo_id: The ID of the todo to delete

    Returns:
        Success message or error
    """
    db = await get_db()

    cursor = await db.execute("SELECT title FROM todos WHERE id = ?", (todo_id,))
    row = await cursor.fetchone()

    if not row:
        return f"Error: Todo #{todo_id} not found."

    await db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    await db.commit()

    return f"✓ Deleted: {row['title']}"


# ============================================================================
# GOAL OPERATIONS
# ============================================================================


async def set_goal(goal: str, timeframe: str, category: str = "general") -> str:
    """Set a new goal.

    Args:
        goal: The goal description
        timeframe: When you want to achieve this
        category: Category of the goal

    Returns:
        Success message
    """
    db = await get_db()

    await db.execute(
        "INSERT INTO goals (goal, timeframe, category) VALUES (?, ?, ?)",
        (goal, timeframe, category),
    )
    await db.commit()

    return f"✓ Set goal: {goal} ({timeframe}, {category})"


async def list_goals(status: str = "active") -> str:
    """List all goals.

    Args:
        status: Filter by 'active' or 'all'

    Returns:
        Formatted list of goals
    """
    db = await get_db()

    if status == "all":
        cursor = await db.execute("SELECT * FROM goals ORDER BY created_at DESC")
    else:
        cursor = await db.execute(
            "SELECT * FROM goals WHERE status = ? ORDER BY created_at DESC", (status,)
        )

    rows = await cursor.fetchall()

    if not rows:
        return f"No {status} goals found."

    result = f"\n=== {status.upper()} GOALS ===\n\n"

    # Group by timeframe
    timeframes = {}
    for row in rows:
        tf = row["timeframe"]
        if tf not in timeframes:
            timeframes[tf] = []
        timeframes[tf].append(row)

    for timeframe, goals in timeframes.items():
        result += f"{timeframe.upper()}:\n"
        for goal in goals:
            result += f"  [{goal['id']}] {goal['goal']} ({goal['category']})\n"
        result += "\n"

    return result.strip()


# ============================================================================
# USER FACTS OPERATIONS
# ============================================================================


async def add_user_fact(fact: str, category: str = "general") -> str:
    """Remember an important fact about the user.

    Args:
        fact: The fact to remember
        category: Category of the fact

    Returns:
        Success message
    """
    db = await get_db()

    await db.execute(
        "INSERT INTO user_facts (fact, category) VALUES (?, ?)", (fact, category)
    )
    await db.commit()

    return f"✓ Remembered: {fact} (category: {category})"


async def get_user_context() -> str:
    """Get relevant context about the user.

    Returns:
        Formatted user context
    """
    db = await get_db()

    cursor = await db.execute(
        "SELECT fact, category FROM user_facts ORDER BY created_at DESC LIMIT 20"
    )
    rows = await cursor.fetchall()

    if not rows:
        return "No user facts stored yet. Use add_user_fact() to remember important information."

    result = "\n=== USER CONTEXT ===\n\n"

    # Group by category
    categories = {}
    for row in rows:
        cat = row["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(row["fact"])

    for category, facts in categories.items():
        result += f"{category.upper()}:\n"
        for fact in facts:
            result += f"  - {fact}\n"
        result += "\n"

    return result.strip()


# ============================================================================
# ACCOMPLISHMENTS OPERATIONS
# ============================================================================


async def log_accomplishment(description: str) -> str:
    """Log something the user accomplished.

    Args:
        description: What the user accomplished

    Returns:
        Success message
    """
    db = await get_db()

    await db.execute(
        "INSERT INTO accomplishments (description) VALUES (?)", (description,)
    )
    await db.commit()

    return f"✓ Logged accomplishment: {description}"
