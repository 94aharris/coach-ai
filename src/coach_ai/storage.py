"""Database storage layer for Coach AI."""

import os
from pathlib import Path
from typing import Optional

import aiosqlite


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

    return _db


# ============================================================================
# TODO OPERATIONS
# ============================================================================


async def add_todo(title: str, priority: str = "medium", notes: str = "") -> str:
    """Add a new todo item.

    Args:
        title: The todo title/description
        priority: Priority level - 'low', 'medium', or 'high'
        notes: Optional additional notes or context

    Returns:
        Success message
    """
    db = await get_db()

    # Validate priority
    if priority not in ["low", "medium", "high"]:
        priority = "medium"

    await db.execute(
        "INSERT INTO todos (title, priority, notes) VALUES (?, ?, ?)",
        (title, priority, notes),
    )
    await db.commit()

    return f"✓ Added todo: {title} (priority: {priority})"


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
