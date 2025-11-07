"""Daily note creation and management for Coach AI."""

import os
from datetime import datetime
from typing import Optional

from coach_ai.obsidian import ObsidianVault
from coach_ai.storage import get_db


# Global Obsidian vault connection
_vault: Optional[ObsidianVault] = None


def get_vault() -> Optional[ObsidianVault]:
    """Get Obsidian vault connection if configured."""
    global _vault

    if _vault is None:
        vault_path = os.environ.get("OBSIDIAN_VAULT_PATH")
        if vault_path:
            daily_notes_format = os.environ.get(
                "DAILY_NOTES_FORMAT", "Daily Notes/{date}.md"
            )
            try:
                _vault = ObsidianVault(vault_path, daily_notes_format)
            except ValueError as e:
                print(f"Warning: Could not initialize Obsidian vault: {e}")
                return None

    return _vault


# ============================================================================
# DAILY NOTE OPERATIONS
# ============================================================================


async def start_my_day(date_str: str = None) -> str:
    """Start your day with a comprehensive overview.

    This tool:
    - Reviews all active todos from the database
    - Reads yesterday's daily note (if it exists)
    - Reads or creates today's daily note
    - Returns all data for the LLM to provide a personalized summary

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Comprehensive context for the LLM to generate a daily briefing
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured. Set OBSIDIAN_VAULT_PATH environment variable."

    # Parse date
    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Invalid date format. Use YYYY-MM-DD, got: {date_str}"
    else:
        date = datetime.now()

    db = await get_db()

    # Build comprehensive context
    context = "=== START MY DAY BRIEFING ===\n\n"
    context += f"Date: {date.strftime('%A, %B %d, %Y')}\n\n"

    # 1. Get all active todos from database
    todos_cursor = await db.execute(
        """
        SELECT id, title, priority, notes, created_at
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

    if todos:
        context += "📋 ACTIVE TODOS:\n"
        for todo in todos:
            context += f"  [{todo['id']}] {todo['title']} (priority: {todo['priority']})\n"
            if todo['notes']:
                context += f"      Notes: {todo['notes']}\n"
        context += "\n"
    else:
        context += "📋 ACTIVE TODOS: None\n\n"

    # 2. Get active goals
    goals_cursor = await db.execute(
        "SELECT goal, timeframe, category FROM goals WHERE status = 'active' ORDER BY created_at DESC"
    )
    goals = await goals_cursor.fetchall()

    if goals:
        context += "🎯 ACTIVE GOALS:\n"
        for goal in goals:
            context += f"  - {goal['goal']} ({goal['timeframe']}, {goal['category']})\n"
        context += "\n"

    # 3. Get user facts/patterns
    facts_cursor = await db.execute(
        "SELECT fact, category FROM user_facts ORDER BY created_at DESC LIMIT 10"
    )
    facts = await facts_cursor.fetchall()

    if facts:
        context += "🧠 WHAT I KNOW ABOUT YOU:\n"
        for fact in facts:
            context += f"  - {fact['fact']} ({fact['category']})\n"
        context += "\n"

    # 4. Read yesterday's note
    from datetime import timedelta
    yesterday = date - timedelta(days=1)

    if vault.daily_note_exists(yesterday):
        yesterday_note = vault.read_daily_note(yesterday)
        if yesterday_note:
            context += f"📖 YESTERDAY'S NOTE ({yesterday.strftime('%Y-%m-%d')}):\n\n"

            # Show tasks from yesterday
            if yesterday_note['tasks']:
                completed = [t for t in yesterday_note['tasks'] if t['completed']]
                incomplete = [t for t in yesterday_note['tasks'] if not t['completed']]

                if completed:
                    context += f"  ✅ Completed ({len(completed)} tasks):\n"
                    for task in completed[:5]:
                        context += f"    - {task['text']}\n"
                    if len(completed) > 5:
                        context += f"    ... and {len(completed) - 5} more\n"
                    context += "\n"

                if incomplete:
                    context += f"  ⏸️ Incomplete ({len(incomplete)} tasks):\n"
                    for task in incomplete[:5]:
                        context += f"    - {task['text']}\n"
                    if len(incomplete) > 5:
                        context += f"    ... and {len(incomplete) - 5} more\n"
                    context += "\n"

            # Show accomplishments
            if yesterday_note['accomplishments']:
                context += "  💪 Accomplishments:\n"
                for acc in yesterday_note['accomplishments'][:5]:
                    context += f"    - {acc}\n"
                context += "\n"
    else:
        context += f"📖 YESTERDAY'S NOTE: No note found for {yesterday.strftime('%Y-%m-%d')}\n\n"

    # 5. Check if today's note exists, create if not
    today_note_existed = vault.daily_note_exists(date)

    if not today_note_existed:
        context += "📝 TODAY'S NOTE: Creating new daily note...\n\n"
        # Create the note (reuse existing logic)
        await create_daily_note(date_str)
    else:
        context += "📝 TODAY'S NOTE: Already exists\n\n"

    # 6. Read today's note
    today_note = vault.read_daily_note(date)
    if today_note:
        if today_note['tasks']:
            context += f"  📋 Tasks planned for today ({len(today_note['tasks'])} total):\n"
            for task in today_note['tasks'][:10]:
                status = "✅" if task['completed'] else "⬜"
                context += f"    {status} {task['text']}\n"
            if len(today_note['tasks']) > 10:
                context += f"    ... and {len(today_note['tasks']) - 10} more\n"

        context += f"\n  Path: {today_note['path']}\n"

    context += "\n"
    context += "=== BRIEFING REQUEST ===\n\n"
    context += (
        "Based on the above information, provide a personalized daily briefing that:\n"
        "1. Welcomes the user and acknowledges yesterday's progress (if any)\n"
        "2. Highlights incomplete tasks from yesterday that might need attention\n"
        "3. Suggests what to focus on first today based on priorities and goals\n"
        "4. Provides motivation and considers ADHD-friendly approaches:\n"
        "   - Start with a quick win to build momentum\n"
        "   - Break down overwhelming tasks\n"
        "   - Acknowledge energy levels and patterns\n"
        "5. Keep it concise, actionable, and encouraging\n"
    )

    return context


async def create_daily_note(date_str: str = None) -> str:
    """Create today's (or specified) daily note with smart population.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Success message with details
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured. Set OBSIDIAN_VAULT_PATH environment variable."

    # Parse date
    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Invalid date format. Use YYYY-MM-DD, got: {date_str}"
    else:
        date = datetime.now()

    # Check if note already exists
    if vault.daily_note_exists(date):
        note_path = vault.get_daily_note_path(date)
        return f"ℹ️  Daily note already exists: {note_path}"

    # Generate smart content
    db = await get_db()

    # 1. Get yesterday's incomplete tasks (if yesterday's note exists)
    yesterday = date.replace(day=date.day - 1) if date.day > 1 else None
    yesterday_tasks = []

    if yesterday and vault.daily_note_exists(yesterday):
        yesterday_note = vault.read_daily_note(yesterday)
        if yesterday_note:
            yesterday_tasks = [
                task["text"]
                for task in yesterday_note["tasks"]
                if not task["completed"]
            ]

    # 2. Get goal-related tasks
    goals_cursor = await db.execute(
        "SELECT goal, timeframe FROM goals WHERE status = 'active' LIMIT 3"
    )
    goals = await goals_cursor.fetchall()

    # 3. Get user patterns for context
    facts_cursor = await db.execute(
        "SELECT fact, category FROM user_facts ORDER BY created_at DESC LIMIT 5"
    )
    facts = await facts_cursor.fetchall()

    # 4. Build tasks list
    tasks = []

    if yesterday_tasks:
        tasks.append("### Carried Over from Yesterday")
        for task in yesterday_tasks[:3]:  # Limit to 3
            tasks.append(task)
        tasks.append("")

    if goals:
        tasks.append("### From Your Goals")
        for goal in goals:
            # Simple task suggestion based on goal
            tasks.append(f"Work on: {goal['goal']} ({goal['timeframe']})")
        tasks.append("")

    # Add low-effort tasks section
    tasks.append("### Low-Effort Tasks")
    tasks.append("<!-- Add easy tasks for low-energy moments -->")

    tasks_text = "\n".join(tasks) if tasks else None

    # 5. Generate focus
    day_name = date.strftime("%A")
    if yesterday_tasks:
        focus = f"**Main Goal:** Continue momentum from yesterday\n**Backup Goal:** If stuck, work on goals instead"
    elif goals:
        focus = f"**Main Goal:** {goals[0]['goal']}\n**Backup Goal:** Make progress on any active goal"
    else:
        focus = "**Main Goal:** Define your priorities for today\n**Backup Goal:** Review and set your goals"

    # 6. Generate quick win (lowest activation energy task)
    current_hour = datetime.now().hour
    is_late_start = current_hour > 10
    is_monday = day_name == "Monday"

    if is_late_start or is_monday:
        quick_win = "Open your todo list and read through it (just look, don't do anything yet)"
    else:
        quick_win = "Review yesterday's accomplishments and choose your first task"

    # 7. Generate context
    context_parts = []

    if not vault.daily_note_exists(date):
        context_parts.append(
            "I noticed you haven't created your daily note yet, so I did it for you."
        )

    if yesterday_tasks:
        context_parts.append(
            f"I pulled in {len(yesterday_tasks)} incomplete tasks from yesterday."
        )

    if goals:
        context_parts.append(
            f"I added tasks related to your active goals: {', '.join(g['goal'] for g in goals[:2])}."
        )

    if facts:
        context_parts.append("\n**What I know about you:**")
        for fact in facts[:3]:
            context_parts.append(f"- {fact['fact']}")

    if is_monday:
        context_parts.append(
            "\n**Pattern note:** It's Monday. I've added an extra-small quick win to help you get started."
        )

    if is_late_start:
        context_parts.append(
            f"\n**Pattern note:** It's {datetime.now().strftime('%I:%M%p').lower()} - later than usual. No judgment! Let's start small."
        )

    context = "\n".join(context_parts) if context_parts else None

    # Create the note
    note_path = vault.create_daily_note(
        date=date,
        focus=focus,
        quick_win=quick_win,
        tasks=tasks_text.split("\n") if tasks_text else None,
        context=context,
    )

    result = f"✅ Created daily note: {note_path}\n\n"

    if yesterday_tasks:
        result += f"📋 Carried over {len(yesterday_tasks)} tasks from yesterday\n"

    if goals:
        result += f"🎯 Added tasks for {len(goals)} active goals\n"

    result += f"\n⚡ Quick win to start: {quick_win}\n"
    result += f"\n🎯 Today's focus:\n{focus}"

    return result


async def sync_from_daily_note(date_str: str = None) -> str:
    """Read today's (or specified) daily note and sync tasks.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Summary of tasks and accomplishments
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured. Set OBSIDIAN_VAULT_PATH environment variable."

    # Parse date
    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%M-%d")
        except ValueError:
            return f"❌ Invalid date format. Use YYYY-MM-DD, got: {date_str}"
    else:
        date = datetime.now()

    # Read note
    note_data = vault.read_daily_note(date)

    if not note_data:
        return f"ℹ️  No daily note found for {date.strftime('%Y-%m-%d')}. Want me to create one?"

    # Extract data
    tasks = note_data["tasks"]
    accomplishments = note_data["accomplishments"]

    # Build response
    result = f"📖 Read daily note: {note_data['path']}\n\n"

    if tasks:
        active_tasks = [t for t in tasks if not t["completed"]]
        completed_tasks = [t for t in tasks if t["completed"]]

        result += f"**Active Tasks:** {len(active_tasks)}\n"
        for task in active_tasks[:5]:  # Show first 5
            priority_emoji = (
                "🔴"
                if task["priority"] == "high"
                else "🟡" if task["priority"] == "medium" else "🔵"
            )
            result += f"{priority_emoji} {task['text']}\n"

        if len(active_tasks) > 5:
            result += f"... and {len(active_tasks) - 5} more\n"

        result += f"\n**Completed Today:** {len(completed_tasks)}\n"

    else:
        result += "No tasks found in daily note.\n"

    if accomplishments:
        result += f"\n**Accomplishments:** {len(accomplishments)}\n"
        for acc in accomplishments[:3]:
            result += f"✅ {acc}\n"

    return result


async def get_daily_note_path(date_str: str = None) -> str:
    """Get the file path to today's (or specified) daily note.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Path and existence status
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured."

    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Invalid date format: {date_str}"
    else:
        date = datetime.now()

    note_path = vault.get_daily_note_path(date)
    exists = note_path.exists()

    result = f"📄 Daily note path: {note_path}\n"
    result += f"Status: {'✅ Exists' if exists else '❌ Does not exist'}\n"

    if not exists:
        result += "\nWant me to create it? Just ask: 'Create my daily note'"

    return result


async def read_daily_note_full(date_str: str = None) -> str:
    """Read the entire daily note including all content and sections.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Full note content with metadata and all sections
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured."

    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Invalid date format: {date_str}"
    else:
        date = datetime.now()

    note_data = vault.read_full_note(date)

    if not note_data:
        return f"❌ No daily note found for {date.strftime('%Y-%m-%d')}."

    result = f"📖 Daily Note: {note_data['path']}\n\n"

    # Show metadata
    if note_data["metadata"]:
        result += "**Metadata:**\n"
        for key, value in note_data["metadata"].items():
            result += f"  {key}: {value}\n"
        result += "\n"

    # Show all sections
    result += "**Sections:**\n"
    for section_name, section_content in note_data["sections"].items():
        result += f"\n### {section_name}\n"
        # Limit content display to avoid overwhelming output
        if len(section_content) > 500:
            result += (
                section_content[:500]
                + "...\n(content truncated, use read_daily_note_section for full text)"
            )
        else:
            result += section_content + "\n"

    return result


async def read_daily_note_section(date_str: str = None, section: str = "Notes") -> str:
    """Read a specific section from the daily note.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
        section: Name of the section to read

    Returns:
        Content of that section
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured."

    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Invalid date format: {date_str}"
    else:
        date = datetime.now()

    section_content = vault.read_section(date, section)

    if section_content is None:
        return f"❌ Section '{section}' not found in daily note for {date.strftime('%Y-%m-%d')}."

    return f"## {section}\n\n{section_content}"


async def write_daily_note_section(
    section: str, content: str, date_str: str = None, append: bool = True
) -> str:
    """Write or append content to a specific section in the daily note.

    Args:
        section: Name of the section to write to
        content: Content to write
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
        append: If True, append to existing content. If False, replace it.

    Returns:
        Confirmation message
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured."

    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Invalid date format: {date_str}"
    else:
        date = datetime.now()

    success = vault.write_to_section(date, section, content, append=append)

    if not success:
        return f"❌ Failed to write to section '{section}'. Section may not exist."

    action = "Appended to" if append else "Updated"
    return f"✅ {action} section '{section}' in daily note for {date.strftime('%Y-%m-%d')}."


async def add_daily_note_section(
    section_name: str, content: str, date_str: str = None, emoji: str = ""
) -> str:
    """Add a new section to the daily note.

    Args:
        section_name: Name for the new section
        content: Initial content for the section
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
        emoji: Optional emoji to prefix the section heading

    Returns:
        Confirmation message
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured."

    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Invalid date format: {date_str}"
    else:
        date = datetime.now()

    success = vault.add_section(date, section_name, content, emoji=emoji)

    if not success:
        return f"❌ Failed to add section '{section_name}'. Daily note may not exist."

    return f"✅ Added new section '{section_name}' to daily note for {date.strftime('%Y-%m-%d')}."


async def generate_daily_summary(date_str: str = None) -> str:
    """Generate an end-of-day summary based on the daily note.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Generated summary with insights and recommendations
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured."

    if date_str:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Invalid date format: {date_str}"
    else:
        date = datetime.now()

    # Read full note
    note_data = vault.read_full_note(date)

    if not note_data:
        return f"❌ No daily note found for {date.strftime('%Y-%m-%d')}."

    # Extract key information
    tasks_section = note_data["sections"].get(
        "Tasks", note_data["sections"].get("✅ Tasks", "")
    )
    accomplishments_section = note_data["sections"].get(
        "Accomplishments", note_data["sections"].get("💪 Accomplishments", "")
    )
    notes_section = note_data["sections"].get(
        "Notes", note_data["sections"].get("📝 Notes", "")
    )

    # Parse tasks
    completed_tasks = []
    incomplete_tasks = []

    for line in tasks_section.split("\n"):
        if "- [x]" in line:
            completed_tasks.append(line.replace("- [x]", "").strip())
        elif "- [ ]" in line:
            incomplete_tasks.append(line.replace("- [ ]", "").strip())

    # Build summary
    summary = f"# Summary for {date.strftime('%A, %B %d, %Y')}\n\n"

    # Completion stats
    total_tasks = len(completed_tasks) + len(incomplete_tasks)
    if total_tasks > 0:
        completion_rate = (len(completed_tasks) / total_tasks) * 100
        summary += f"## 📊 Completion Rate: {completion_rate:.0f}%\n"
        summary += f"- Completed: {len(completed_tasks)}/{total_tasks} tasks\n\n"
    else:
        summary += "## 📊 No tasks tracked today\n\n"

    # Accomplishments
    if completed_tasks or accomplishments_section.strip():
        summary += "## ✅ What Went Well\n"
        if completed_tasks:
            for task in completed_tasks[:5]:
                if task and not task.startswith("#"):
                    summary += f"- {task}\n"
        if accomplishments_section.strip():
            summary += f"\n{accomplishments_section}\n"
        summary += "\n"

    # Incomplete tasks
    if incomplete_tasks:
        summary += "## ⏸️ Carried Over\n"
        summary += f"{len(incomplete_tasks)} tasks to consider for tomorrow:\n"
        for task in incomplete_tasks[:3]:
            if task and not task.startswith("#"):
                summary += f"- {task}\n"
        summary += "\n"

    # Key insights from notes
    if notes_section.strip():
        summary += "## 💭 Key Notes\n"
        # Take first few lines of notes as highlights
        note_lines = [
            line.strip()
            for line in notes_section.split("\n")
            if line.strip() and not line.strip().startswith("<!--")
        ]
        for line in note_lines[:3]:
            summary += f"- {line}\n"
        summary += "\n"

    # Recommendations
    summary += "## 🎯 Recommendations\n"
    if len(incomplete_tasks) > 5:
        summary += "- Consider breaking down or delegating some tasks - you have quite a few incomplete items\n"
    if len(completed_tasks) > 3:
        summary += "- Great productivity today! Maintain this momentum\n"
    if not completed_tasks and not incomplete_tasks:
        summary += "- Start tracking your tasks in the daily note for better visibility\n"

    summary += f"\n_Generated at {datetime.now().strftime('%I:%M%p').lower()}_"

    return summary
