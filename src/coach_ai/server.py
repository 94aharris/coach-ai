"""Coach AI MCP Server - ADHD coaching assistant."""

import os
from pathlib import Path

import aiosqlite
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Coach AI")

# Global database connection
_db = None


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
# TODO MANAGEMENT TOOLS
# ============================================================================


@mcp.tool()
async def add_todo(title: str, priority: str = "medium", notes: str = "") -> str:
    """Add a new todo item.

    Args:
        title: The todo title/description
        priority: Priority level - 'low', 'medium', or 'high' (default: 'medium')
        notes: Optional additional notes or context
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


@mcp.tool()
async def list_todos(status: str = "active") -> str:
    """List todos filtered by status.

    Args:
        status: Filter by 'active', 'completed', or 'all' (default: 'active')
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


@mcp.tool()
async def complete_todo(todo_id: int) -> str:
    """Mark a todo as complete.

    Args:
        todo_id: The ID of the todo to complete
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


@mcp.tool()
async def delete_todo(todo_id: int) -> str:
    """Delete a todo permanently.

    Args:
        todo_id: The ID of the todo to delete
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
# GOAL MANAGEMENT TOOLS
# ============================================================================


@mcp.tool()
async def set_goal(goal: str, timeframe: str, category: str = "general") -> str:
    """Set a new goal.

    Args:
        goal: The goal description
        timeframe: When you want to achieve this (e.g., 'this week', 'this month', 'long-term')
        category: Category of the goal (e.g., 'career', 'health', 'personal', 'general')
    """
    db = await get_db()

    await db.execute(
        "INSERT INTO goals (goal, timeframe, category) VALUES (?, ?, ?)",
        (goal, timeframe, category),
    )
    await db.commit()

    return f"✓ Set goal: {goal} ({timeframe}, {category})"


@mcp.tool()
async def list_goals(status: str = "active") -> str:
    """List all goals.

    Args:
        status: Filter by 'active' or 'all' (default: 'active')
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
# USER CONTEXT & LEARNING TOOLS
# ============================================================================


@mcp.tool()
async def add_user_fact(fact: str, category: str = "general") -> str:
    """Remember an important fact about the user.

    Use this to remember preferences, patterns, challenges, strengths, routines, etc.
    These facts help personalize recommendations and support.

    Args:
        fact: The fact to remember (e.g., "Works best in mornings", "Struggles with context switching")
        category: Category - 'preferences', 'challenges', 'strengths', 'patterns', 'routines', or 'general'
    """
    db = await get_db()

    await db.execute(
        "INSERT INTO user_facts (fact, category) VALUES (?, ?)", (fact, category)
    )
    await db.commit()

    return f"✓ Remembered: {fact} (category: {category})"


@mcp.tool()
async def get_user_context() -> str:
    """Get relevant context about the user (facts, patterns, preferences).

    This retrieves stored facts about the user to help personalize responses.
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


@mcp.tool()
async def log_accomplishment(description: str) -> str:
    """Log something the user accomplished.

    This helps track progress and provides positive reinforcement.

    Args:
        description: What the user accomplished
    """
    db = await get_db()

    await db.execute(
        "INSERT INTO accomplishments (description) VALUES (?)", (description,)
    )
    await db.commit()

    return f"✓ Logged accomplishment: {description}"


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================


@mcp.tool()
async def get_recommendation() -> str:
    """Get a personalized recommendation for what to do next.

    This analyzes the user's current todos, goals, recent activity, and known facts
    to suggest the most appropriate next action. This is the core "What should I do now?"
    feature designed to help with decision paralysis.
    """
    db = await get_db()

    # Get active todos
    todos_cursor = await db.execute(
        """
        SELECT id, title, priority, notes
        FROM todos
        WHERE status = 'active'
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END,
            created_at ASC
        """
    )
    todos = await todos_cursor.fetchall()

    # Get goals
    goals_cursor = await db.execute(
        "SELECT goal, timeframe, category FROM goals WHERE status = 'active' ORDER BY created_at DESC"
    )
    goals = await goals_cursor.fetchall()

    # Get user facts
    facts_cursor = await db.execute(
        "SELECT fact, category FROM user_facts ORDER BY created_at DESC LIMIT 10"
    )
    facts = await facts_cursor.fetchall()

    # Get recent accomplishments
    accomplishments_cursor = await db.execute(
        "SELECT description, created_at FROM accomplishments ORDER BY created_at DESC LIMIT 5"
    )
    accomplishments = await accomplishments_cursor.fetchall()

    # Build comprehensive context
    context = "=== CURRENT STATE FOR RECOMMENDATION ===\n\n"

    # Todos section
    if todos:
        context += "ACTIVE TODOS:\n"
        for i, todo in enumerate(todos[:10], 1):  # Limit to top 10
            context += f"  {i}. [{todo['id']}] {todo['title']} (priority: {todo['priority']})\n"
            if todo["notes"]:
                context += f"      Notes: {todo['notes']}\n"
    else:
        context += "ACTIVE TODOS: None\n"

    context += "\n"

    # Goals section
    if goals:
        context += "ACTIVE GOALS:\n"
        for goal in goals:
            context += (
                f"  - {goal['goal']} ({goal['timeframe']}, {goal['category']})\n"
            )
    else:
        context += "ACTIVE GOALS: None set yet\n"

    context += "\n"

    # User context section
    if facts:
        context += "KNOWN ABOUT USER:\n"
        for fact in facts:
            context += f"  - {fact['fact']} ({fact['category']})\n"
    else:
        context += "KNOWN ABOUT USER: Learning about you as we go\n"

    context += "\n"

    # Recent wins section
    if accomplishments:
        context += "RECENT ACCOMPLISHMENTS:\n"
        for acc in accomplishments:
            context += f"  - {acc['description']}\n"

    context += "\n"
    context += "=== RECOMMENDATION REQUEST ===\n\n"
    context += (
        "Based on the above context, provide a specific, actionable recommendation for what "
        "the user should focus on RIGHT NOW. Consider:\n"
        "- Their priorities and goals\n"
        "- Known patterns and preferences\n"
        "- ADHD considerations (decision paralysis, activation energy, time blindness)\n"
        "- The need for clear, concrete next steps\n"
        "- Breaking down overwhelming tasks\n\n"
        "If there are no active todos, encourage the user to add some or reflect on their goals."
    )

    return context


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
