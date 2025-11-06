"""Recommendation engine for Coach AI."""

from coach_ai.storage import get_db


async def get_recommendation() -> str:
    """Get a personalized recommendation for what to do next.

    Analyzes the user's current todos, goals, recent activity, and known facts
    to suggest the most appropriate next action.

    Returns:
        Context string for AI to generate recommendation from
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
            context += f"  - {goal['goal']} ({goal['timeframe']}, {goal['category']})\n"
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
