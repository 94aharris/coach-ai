"""Coach AI MCP Server - ADHD coaching assistant."""

from mcp.server.fastmcp import FastMCP

from coach_ai import daily_notes, recommendations, storage

# Initialize FastMCP server
mcp = FastMCP("Coach AI")


# ============================================================================
# TODO MANAGEMENT TOOLS
# ============================================================================


@mcp.tool()
async def add_todo(title: str, priority: str = "medium", notes: str = "", quick: bool = False) -> str:
    """Add a new todo item with smart categorization.

    Args:
        title: The todo title/description
        priority: Priority level - 'low', 'medium', or 'high' (default: 'medium')
        notes: Optional additional notes or context
        quick: Mark as quick win for low-energy moments (auto-sets low priority)
    """
    return await storage.add_todo(title, priority, notes, quick)


@mcp.tool()
async def list_todos(status: str = "active") -> str:
    """List todos filtered by status.

    Args:
        status: Filter by 'active', 'completed', or 'all' (default: 'active')
    """
    return await storage.list_todos(status)


@mcp.tool()
async def complete_todo(todo_id: int) -> str:
    """Mark a todo as complete.

    Args:
        todo_id: The ID of the todo to complete
    """
    return await storage.complete_todo(todo_id)


@mcp.tool()
async def delete_todo(todo_id: int) -> str:
    """Delete a todo permanently.

    Args:
        todo_id: The ID of the todo to delete
    """
    return await storage.delete_todo(todo_id)


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
    return await storage.set_goal(goal, timeframe, category)


@mcp.tool()
async def list_goals(status: str = "active") -> str:
    """List all goals.

    Args:
        status: Filter by 'active' or 'all' (default: 'active')
    """
    return await storage.list_goals(status)


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
    return await storage.add_user_fact(fact, category)


@mcp.tool()
async def get_user_context() -> str:
    """Get relevant context about the user (facts, patterns, preferences).

    This retrieves stored facts about the user to help personalize responses.
    """
    return await storage.get_user_context()


@mcp.tool()
async def log_accomplishment(description: str) -> str:
    """Log something the user accomplished.

    This helps track progress and provides positive reinforcement.

    Args:
        description: What the user accomplished
    """
    return await storage.log_accomplishment(description)


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
    return await recommendations.get_recommendation()


# ============================================================================
# OBSIDIAN INTEGRATION TOOLS
# ============================================================================


@mcp.tool()
async def start_my_day(date_str: str = None) -> str:
    """Start your day with smart task selection and daily note creation.

    ENHANCED - Obsidian-first workflow:
    - Syncs yesterday's completed tasks from daily note
    - Intelligently selects 3-5 tasks from backlog using deterministic algorithm
    - Creates today's daily note with selected tasks organized by priority
    - Returns comprehensive briefing for the day

    Selection algorithm picks:
    - 1 critical task (deadlines or highest priority)
    - 1-2 important tasks (high-impact work)
    - 2-3 quick wins (low-effort, high-dopamine)

    Perfect for: "Start my day" or "What should I focus on today?"

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Daily briefing with selected tasks, goals, and motivational message
    """
    return await daily_notes.start_my_day(date_str)


@mcp.tool()
async def sync_daily_note(date_str: str = None) -> str:
    """Sync completed tasks from Obsidian daily note to database.

    NEW TOOL - Bidirectional sync:
    Reads markdown checkboxes (- [x]) from your daily note and automatically
    marks matching todos as complete in the database. Uses fuzzy matching to
    handle partial text matches.

    This enables an Obsidian-first workflow: work in your daily note, check
    off tasks there, then sync back to Coach AI's database.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Summary of tasks synced and any warnings about unmatched checkboxes
    """
    return await daily_notes.sync_daily_note(date_str)


@mcp.tool()
async def create_daily_note(date_str: str = None) -> str:
    """Create today's (or specified) daily note with smart population.

    Automatically pulls in:
    - Incomplete tasks from yesterday
    - Tasks related to active goals
    - A "quick win" task for low-motivation days
    - Context and insights

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
    """
    return await daily_notes.create_daily_note(date_str)


@mcp.tool()
async def sync_from_daily_note(date_str: str = None) -> str:
    """Read today's (or specified) daily note and sync tasks.

    Extracts tasks from your daily note and ensures they're in the system.
    Call this to refresh Coach AI's view of your daily note.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
    """
    return await daily_notes.sync_from_daily_note(date_str)


@mcp.tool()
async def get_daily_note_path(date_str: str = None) -> str:
    """Get the file path to today's (or specified) daily note.

    Useful for opening the note in Obsidian or checking if it exists.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
    """
    return await daily_notes.get_daily_note_path(date_str)


@mcp.tool()
async def read_daily_note_full(date_str: str = None) -> str:
    """Read the entire daily note including all content and sections.

    This gives you complete access to the note for analysis, summarization,
    or extracting information from any section.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Full note content with metadata and all sections
    """
    return await daily_notes.read_daily_note_full(date_str)


@mcp.tool()
async def read_daily_note_section(date_str: str = None, section: str = "Notes") -> str:
    """Read a specific section from the daily note.

    Use this to read any section by name, such as "Notes", "Tasks",
    "Focus for Today", etc.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
        section: Name of the section to read (without ## or emoji)

    Returns:
        Content of that section
    """
    return await daily_notes.read_daily_note_section(date_str, section)


@mcp.tool()
async def write_daily_note_section(
    section: str, content: str, date_str: str = None, append: bool = True
) -> str:
    """Write or append content to a specific section in the daily note.

    Use this to add summaries, insights, reflections, or any other content
    to specific sections of your daily note.

    Args:
        section: Name of the section to write to (e.g., "Notes", "Coach AI Insights")
        content: Content to write
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
        append: If True, append to existing content. If False, replace it.

    Returns:
        Confirmation message
    """
    return await daily_notes.write_daily_note_section(section, content, date_str, append)


@mcp.tool()
async def add_daily_note_section(
    section_name: str, content: str, date_str: str = None, emoji: str = ""
) -> str:
    """Add a new section to the daily note.

    Creates a new section with a heading and initial content.

    Args:
        section_name: Name for the new section
        content: Initial content for the section
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
        emoji: Optional emoji to prefix the section heading (e.g., "📊", "💡")

    Returns:
        Confirmation message
    """
    return await daily_notes.add_daily_note_section(section_name, content, date_str, emoji)


@mcp.tool()
async def generate_daily_summary(date_str: str = None) -> str:
    """Generate an end-of-day summary based on the daily note.

    Analyzes the day's tasks, accomplishments, notes, and provides insights.
    This summary can be added back to the daily note or used to plan tomorrow.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Generated summary with insights and recommendations
    """
    return await daily_notes.generate_daily_summary(date_str)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
