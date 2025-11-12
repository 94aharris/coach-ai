"""Daily note creation and management for Coach AI."""

import os
from datetime import datetime, date, timedelta
from typing import Optional
from difflib import SequenceMatcher

import aiosqlite

from coach_ai.obsidian import ObsidianVault
from coach_ai.storage import get_db
from coach_ai.task_selection import select_tasks_for_today, increment_skip_counts


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
    """Start your day with smart task selection and daily note creation.

    ENHANCED VERSION - Obsidian-first workflow:
    - Syncs yesterday's completed tasks from daily note
    - Intelligently selects 3-5 tasks from backlog
    - Creates or updates today's daily note with selected tasks
    - Returns comprehensive briefing for the day

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Daily briefing with selected tasks and context
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured. Set OBSIDIAN_VAULT_PATH environment variable."

    # Parse date
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return f"❌ Invalid date format. Use YYYY-MM-DD, got: {date_str}"
    else:
        target_date = date.today()

    db = await get_db()

    # Build briefing
    briefing = "=== 🌅 START MY DAY ===\n\n"
    briefing += f"📅 {target_date.strftime('%A, %B %d, %Y')}\n\n"

    # 1. Sync yesterday's note first (mark completed tasks)
    yesterday = target_date - timedelta(days=1)
    if vault.daily_note_exists(datetime.combine(yesterday, datetime.min.time())):
        sync_result = await _sync_completed_tasks(vault, yesterday, db)
        if sync_result["completed_count"] > 0:
            briefing += f"✅ Synced {sync_result['completed_count']} completed tasks from yesterday\n"
            for task in sync_result["completed_tasks"][:3]:
                briefing += f"   - {task}\n"
            if sync_result["completed_count"] > 3:
                briefing += f"   ... and {sync_result['completed_count'] - 3} more\n"
            briefing += "\n"

    # 2. Select tasks for today using smart algorithm
    selected = await select_tasks_for_today(db, target_date, max_tasks=5)

    total_selected = (
        len(selected["critical"]) + len(selected["important"]) + len(selected["quick_wins"])
    )

    briefing += f"📋 Selected {total_selected} tasks from {selected['backlog_count']} in backlog\n\n"

    # 3. Create or update today's daily note
    note_existed = vault.daily_note_exists(datetime.combine(target_date, datetime.min.time()))

    if not note_existed:
        # Create new note with selected tasks
        await _create_daily_note_with_tasks(vault, target_date, selected)
        briefing += f"📝 Created today's daily note\n\n"
    else:
        # Note exists - could update it or leave as-is
        briefing += f"📝 Daily note already exists\n\n"

    # 4. Show selected tasks in briefing
    if selected["critical"]:
        briefing += "🎯 **CRITICAL (Do This First)**\n"
        for task in selected["critical"]:
            briefing += f"   [{task['id']}] {task['title']}\n"
            if task.get("notes"):
                briefing += f"       Note: {task['notes'][:100]}\n"
        briefing += "\n"

    if selected["important"]:
        briefing += "🔥 **IMPORTANT (Pick 1-2)**\n"
        for task in selected["important"]:
            briefing += f"   [{task['id']}] {task['title']}\n"
        briefing += "\n"

    if selected["quick_wins"]:
        briefing += "⚡ **QUICK WINS (Energy Permitting)**\n"
        for task in selected["quick_wins"]:
            time_str = f" ({task['time_estimate']}min)" if task.get("time_estimate") else ""
            briefing += f"   [{task['id']}] {task['title']}{time_str}\n"
        briefing += "\n"

    # 5. Get active goals for context
    goals_cursor = await db.execute(
        "SELECT goal, timeframe FROM goals WHERE status = 'active' LIMIT 3"
    )
    goals = await goals_cursor.fetchall()

    if goals:
        briefing += "🎯 **Active Goals**\n"
        for goal in goals:
            briefing += f"   - {goal['goal']} ({goal['timeframe']})\n"
        briefing += "\n"

    # 6. Add note path
    note_path = vault.get_daily_note_path(datetime.combine(target_date, datetime.min.time()))
    briefing += f"📄 Daily note: {note_path}\n\n"

    # 7. Motivational message
    current_hour = datetime.now().hour
    if current_hour < 12:
        briefing += "💪 Good morning! Start with the critical task or a quick win to build momentum.\n"
    elif current_hour < 17:
        briefing += "💪 Afternoon check-in! Pick one task from the important section.\n"
    else:
        briefing += "💪 Evening session! Focus on quick wins if energy is low.\n"

    return briefing


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


async def sync_daily_note(date_str: str = None) -> str:
    """Sync completed tasks from Obsidian daily note to database.

    NEW TOOL - Bidirectional sync:
    Reads markdown checkboxes from daily note and marks matching
    todos as complete in the database.

    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Summary of synced tasks
    """
    vault = get_vault()
    if not vault:
        return "❌ Obsidian vault not configured."

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return f"❌ Invalid date format: {date_str}"
    else:
        target_date = date.today()

    db = await get_db()

    sync_result = await _sync_completed_tasks(vault, target_date, db)

    result = f"📝 Synced daily note for {target_date.strftime('%Y-%m-%d')}\n\n"

    if sync_result["completed_count"] > 0:
        result += f"✅ Marked {sync_result['completed_count']} tasks complete:\n"
        for task in sync_result["completed_tasks"]:
            result += f"   - {task}\n"
    else:
        result += "No new completed tasks found.\n"

    if sync_result["warnings"]:
        result += f"\n⚠️  {len(sync_result['warnings'])} checkboxes couldn't be matched to todos\n"

    return result


async def _sync_completed_tasks(
    vault: ObsidianVault, target_date: date, db: aiosqlite.Connection
) -> dict:
    """Internal helper to sync completed tasks from daily note.

    Returns:
        Dict with completed_count, completed_tasks list, and warnings
    """
    note_data = vault.read_daily_note(datetime.combine(target_date, datetime.min.time()))

    if not note_data:
        return {"completed_count": 0, "completed_tasks": [], "warnings": []}

    completed_checkboxes = [
        task for task in note_data.get("tasks", []) if task.get("completed")
    ]

    if not completed_checkboxes:
        return {"completed_count": 0, "completed_tasks": [], "warnings": []}

    # Get all active todos from database
    cursor = await db.execute(
        "SELECT id, title FROM todos WHERE status = 'active'"
    )
    active_todos = {row["id"]: row["title"] for row in await cursor.fetchall()}

    completed_tasks = []
    warnings = []

    for checkbox in completed_checkboxes:
        checkbox_text = checkbox["text"]

        # Try to match checkbox to a todo
        matched_id = _fuzzy_match_task(checkbox_text, active_todos)

        if matched_id:
            # Mark as complete
            await db.execute(
                "UPDATE todos SET status = 'completed', completed_at = ? WHERE id = ?",
                (datetime.now().isoformat(), matched_id),
            )
            completed_tasks.append(active_todos[matched_id])
        else:
            warnings.append(checkbox_text)

    await db.commit()

    return {
        "completed_count": len(completed_tasks),
        "completed_tasks": completed_tasks,
        "warnings": warnings,
    }


def _fuzzy_match_task(checkbox_text: str, todos: dict) -> Optional[int]:
    """Match checkbox text to a todo using fuzzy matching.

    Args:
        checkbox_text: Text from checkbox (e.g., "IMAGE_TAG env var")
        todos: Dict of {id: title} for all active todos

    Returns:
        ID of matched todo, or None if no good match
    """
    best_match_id = None
    best_ratio = 0.0

    checkbox_lower = checkbox_text.lower().strip()

    for todo_id, todo_title in todos.items():
        title_lower = todo_title.lower().strip()

        # Exact match
        if checkbox_lower == title_lower:
            return todo_id

        # Substring match
        if checkbox_lower in title_lower or title_lower in checkbox_lower:
            return todo_id

        # Fuzzy match
        ratio = SequenceMatcher(None, checkbox_lower, title_lower).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match_id = todo_id

    # Return best match if similarity > 70%
    if best_ratio > 0.7:
        return best_match_id

    return None


async def _create_daily_note_with_tasks(
    vault: ObsidianVault, target_date: date, selected: dict
) -> str:
    """Create daily note with smart task selection.

    Args:
        vault: Obsidian vault instance
        target_date: Date for the note
        selected: Dict from select_tasks_for_today with critical/important/quick_wins

    Returns:
        Path to created note
    """
    # Build sections
    critical_section = ""
    if selected["critical"]:
        critical_section = "## 🎯 Today's Focus (Pick 1)\n\n"
        for task in selected["critical"]:
            critical_section += f"- [ ] {task['title']}\n"
            if task.get("notes"):
                # Add notes as indented comment
                for line in task["notes"].split("\n"):
                    if line.strip():
                        critical_section += f"  > {line}\n"

    important_section = ""
    if selected["important"]:
        important_section = "## 🔥 Important (Pick 1-2)\n\n"
        for task in selected["important"]:
            important_section += f"- [ ] {task['title']}\n"

    quick_wins_section = ""
    if selected["quick_wins"]:
        quick_wins_section = "## ⚡ Quick Wins (Energy Permitting)\n\n"
        for task in selected["quick_wins"]:
            time_str = f" `{task['time_estimate']}min`" if task.get("time_estimate") else ""
            quick_wins_section += f"- [ ] {task['title']}{time_str}\n"

    # Build full content
    day_name = target_date.strftime("%A")
    full_date = target_date.strftime("%B %d, %Y")

    content = f"# {day_name}, {full_date}\n\n"

    if critical_section:
        content += critical_section + "\n"
    if important_section:
        content += important_section + "\n"
    if quick_wins_section:
        content += quick_wins_section + "\n"

    # Add backlog count
    total_selected = (
        len(selected["critical"]) + len(selected["important"]) + len(selected["quick_wins"])
    )
    remaining = selected["backlog_count"] - total_selected
    content += f"## 📋 Backlog\n\n"
    content += f"<!-- {remaining} tasks remaining - run sync_daily_note to update -->\n\n"

    # Add sections
    content += "## 📝 Notes\n\n\n"
    content += "## ✅ Completed Today\n\n<!-- Completed tasks will appear here -->\n"

    # Create note with frontmatter
    metadata = {
        "date": target_date.isoformat(),
        "type": "daily-note",
        "day_of_week": day_name.lower(),
    }

    import frontmatter
    post = frontmatter.Post(content, **metadata)

    note_path = vault.get_daily_note_path(datetime.combine(target_date, datetime.min.time()))
    note_path.parent.mkdir(parents=True, exist_ok=True)

    with open(note_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    return str(note_path)


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
