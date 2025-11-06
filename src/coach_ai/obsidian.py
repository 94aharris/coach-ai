"""Obsidian vault integration - reading and writing daily notes."""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import frontmatter


class ObsidianVault:
    """Manages interactions with an Obsidian vault."""

    def __init__(self, vault_path: str, daily_notes_format: str = "Daily Notes/{date}.md"):
        """Initialize vault connection.

        Args:
            vault_path: Path to Obsidian vault root
            daily_notes_format: Format string for daily notes path (use {date} placeholder)
        """
        self.vault_path = Path(vault_path).expanduser()
        self.daily_notes_format = daily_notes_format

        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

    def get_daily_note_path(self, date: datetime = None) -> Path:
        """Get path to a daily note.

        Args:
            date: Date for the note (defaults to today)

        Returns:
            Path to the daily note file
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        note_path = self.daily_notes_format.replace("{date}", date_str)
        return self.vault_path / note_path

    def daily_note_exists(self, date: datetime = None) -> bool:
        """Check if daily note exists for given date."""
        return self.get_daily_note_path(date).exists()

    def read_daily_note(self, date: datetime = None) -> Optional[dict]:
        """Read and parse a daily note.

        Returns:
            Dict with 'metadata' (frontmatter), 'content' (body), 'tasks', 'accomplishments'
            or None if note doesn't exist
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            return None

        with open(note_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Parse tasks from content
        tasks = self._extract_tasks(post.content)
        accomplishments = self._extract_accomplishments(post.content)

        return {
            "path": str(note_path),
            "metadata": dict(post.metadata),
            "content": post.content,
            "tasks": tasks,
            "accomplishments": accomplishments,
        }

    def _extract_tasks(self, content: str) -> list[dict]:
        """Extract todo items from markdown content.

        Returns list of dicts with: text, completed, priority, tags
        """
        tasks = []

        # Find Tasks section
        task_section = self._extract_section(content, "Tasks")
        if not task_section:
            task_section = self._extract_section(content, "✅ Tasks")

        if not task_section:
            return tasks

        # Parse checkbox items
        # Match: - [ ] Task text #tag #priority
        # or:    - [x] Task text
        pattern = r"^- \[([ x])\] (.+)$"

        for line in task_section.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                completed = match.group(1) == "x"
                task_text = match.group(2).strip()

                # Extract tags
                tags = re.findall(r"#(\w+[-\w]*)", task_text)

                # Extract priority from tags
                priority = "medium"
                if "high-priority" in tags or "urgent" in tags:
                    priority = "high"
                elif "low-priority" in tags:
                    priority = "low"

                # Remove tags from display text
                clean_text = re.sub(r"\s*#\w+[-\w]*", "", task_text).strip()

                tasks.append({
                    "text": clean_text,
                    "completed": completed,
                    "priority": priority,
                    "tags": tags,
                    "raw": line.strip(),
                })

        return tasks

    def _extract_accomplishments(self, content: str) -> list[str]:
        """Extract accomplishments from the Accomplishments section."""
        accomplishments = []

        section = self._extract_section(content, "Accomplishments")
        if not section:
            section = self._extract_section(content, "💪 Accomplishments")

        if not section:
            return accomplishments

        # Parse list items or checked items
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                # Remove list marker and checkbox if present
                text = re.sub(r"^[-*] (\[x\] )?", "", line).strip()
                if text and not text.startswith("<!--"):
                    accomplishments.append(text)

        return accomplishments

    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract content of a markdown section by heading.

        Args:
            content: Full markdown content
            section_name: Section heading to find (without ##)

        Returns:
            Content of that section, or None if not found
        """
        # Match: ## Section Name or ## 🎯 Section Name
        # Capture everything until next ## heading or end of file
        pattern = rf"^##\s+(?:[\U0001F300-\U0001F9FF]\s+)?{re.escape(section_name)}\s*$(.+?)(?=^##\s|\Z)"

        match = re.search(pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        return None

    def create_daily_note(
        self,
        date: datetime = None,
        focus: str = None,
        quick_win: str = None,
        tasks: list[str] = None,
        context: str = None,
    ) -> str:
        """Create a new daily note with smart population.

        Args:
            date: Date for the note (defaults to today)
            focus: Primary focus for the day
            quick_win: Small task to start with
            tasks: List of tasks to include
            context: Coach AI context/insights

        Returns:
            Path to created note
        """
        if date is None:
            date = datetime.now()

        note_path = self.get_daily_note_path(date)

        # Don't overwrite existing note
        if note_path.exists():
            return str(note_path)

        # Ensure directory exists
        note_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate content
        day_name = date.strftime("%A")
        full_date = date.strftime("%B %d, %Y")
        date_str = date.strftime("%Y-%m-%d")

        # Build frontmatter
        metadata = {
            "date": date_str,
            "type": "daily-note",
            "day_of_week": day_name.lower(),
        }

        # Build content
        content_parts = [f"# {day_name}, {full_date}\n"]

        # Focus section
        content_parts.append("## 🎯 Focus for Today")
        if focus:
            content_parts.append(focus)
        else:
            content_parts.append("<!-- What's your main goal for today? -->")
        content_parts.append("")

        # Quick win section
        if quick_win:
            content_parts.append("## ⚡ Quick Win (Start Here)")
            content_parts.append(f"- [ ] {quick_win}")
            content_parts.append("")

        # Tasks section
        content_parts.append("## ✅ Tasks")
        if tasks:
            for task in tasks:
                content_parts.append(f"- [ ] {task}")
        else:
            content_parts.append("<!-- Tasks will appear here -->")
        content_parts.append("")

        # Accomplishments section
        content_parts.append("## 💪 Accomplishments")
        content_parts.append("<!-- You'll add your wins here as you complete things! -->")
        content_parts.append("")

        # Notes section
        content_parts.append("## 📝 Notes")
        content_parts.append("")
        content_parts.append("")

        # Coach AI Insights
        if context:
            content_parts.append("## 🧠 Coach AI Insights")
            content_parts.append(f"Created: {datetime.now().strftime('%I:%M%p').lower()}")
            content_parts.append("")
            content_parts.append(context)
            content_parts.append("")

        body = "\n".join(content_parts)

        # Create frontmatter post
        post = frontmatter.Post(body, **metadata)

        # Write atomically (temp file + rename)
        temp_path = note_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        temp_path.rename(note_path)

        return str(note_path)

    def update_task_status(self, date: datetime, task_text: str, completed: bool) -> bool:
        """Update a task's completion status in daily note.

        Args:
            date: Date of daily note
            task_text: Text of task to update
            completed: Whether task is completed

        Returns:
            True if task was found and updated
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            return False

        with open(note_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Find and replace task
        checkbox = "[x]" if completed else "[ ]"
        old_checkbox = "[ ]" if completed else "[x]"

        # Create pattern to find this specific task
        # Match: - [ ] task_text or - [x] task_text
        pattern = rf"^(- \[{re.escape(old_checkbox[1])}\] )({re.escape(task_text)}.*)$"

        updated = False
        new_lines = []

        for line in post.content.split("\n"):
            match = re.match(pattern, line)
            if match and not updated:
                # Replace checkbox
                new_line = f"- {checkbox} {match.group(2)}"
                new_lines.append(new_line)
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            return False

        post.content = "\n".join(new_lines)

        # Write atomically
        temp_path = note_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        temp_path.rename(note_path)

        return True

    def add_task_to_daily_note(
        self, date: datetime, task_text: str, priority: str = "medium"
    ) -> bool:
        """Add a new task to the daily note.

        Args:
            date: Date of daily note
            task_text: Task text
            priority: Priority level (low/medium/high)

        Returns:
            True if task was added
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            # Create the note first
            self.create_daily_note(date, tasks=[task_text])
            return True

        with open(note_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Find Tasks section
        content = post.content
        tasks_heading = "## ✅ Tasks"

        if tasks_heading not in content:
            tasks_heading = "## Tasks"
            if tasks_heading not in content:
                # Add tasks section
                post.content += f"\n\n{tasks_heading}\n"

        # Add priority tag
        priority_tag = ""
        if priority == "high":
            priority_tag = " #high-priority"
        elif priority == "low":
            priority_tag = " #low-priority"

        # Insert task under Tasks heading
        new_task = f"- [ ] {task_text}{priority_tag}"

        # Find insertion point (after Tasks heading)
        lines = post.content.split("\n")
        new_lines = []
        inserted = False

        for i, line in enumerate(lines):
            new_lines.append(line)

            if not inserted and (line.strip() == "## ✅ Tasks" or line.strip() == "## Tasks"):
                # Insert after heading (and any existing tasks)
                # Find where to insert based on priority
                insert_index = i + 1

                # Skip past higher priority tasks if this is medium/low
                if priority != "high":
                    while insert_index < len(lines) and lines[insert_index].strip().startswith("- [ ]"):
                        if "#high-priority" not in lines[insert_index] or priority == "low":
                            break
                        insert_index += 1
                        new_lines.append(lines[insert_index - 1])

                new_lines.insert(insert_index, new_task)
                inserted = True

        if not inserted:
            return False

        post.content = "\n".join(new_lines)

        # Write atomically
        temp_path = note_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        temp_path.rename(note_path)

        return True

    def add_accomplishment(self, date: datetime, accomplishment: str) -> bool:
        """Add an accomplishment to the daily note.

        Args:
            date: Date of daily note
            accomplishment: Accomplishment text

        Returns:
            True if added successfully
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            return False

        with open(note_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Find Accomplishments section
        content = post.content
        accomplishments_heading = "## 💪 Accomplishments"

        if accomplishments_heading not in content:
            accomplishments_heading = "## Accomplishments"
            if accomplishments_heading not in content:
                return False

        # Add accomplishment
        timestamp = datetime.now().strftime("%I:%M%p").lower()
        new_accomplishment = f"- {accomplishment} ({timestamp})"

        # Insert after heading
        lines = content.split("\n")
        new_lines = []
        inserted = False

        for line in lines:
            new_lines.append(line)

            if not inserted and (
                line.strip() == "## 💪 Accomplishments"
                or line.strip() == "## Accomplishments"
            ):
                # Skip comment line if present
                new_lines.append(new_accomplishment)
                inserted = True

        if not inserted:
            return False

        post.content = "\n".join(new_lines)

        # Write atomically
        temp_path = note_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        temp_path.rename(note_path)

        return True

    def read_full_note(self, date: datetime = None) -> Optional[dict]:
        """Read entire daily note including all content and metadata.

        Returns:
            Dict with 'path', 'metadata', 'full_content', 'sections'
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            return None

        with open(note_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Extract all sections
        sections = self._parse_all_sections(post.content)

        return {
            "path": str(note_path),
            "metadata": dict(post.metadata),
            "full_content": post.content,
            "sections": sections,
        }

    def _parse_all_sections(self, content: str) -> dict[str, str]:
        """Parse all markdown sections in the content.

        Returns dict mapping section names to their content.
        """
        sections = {}

        # Split by ## headings
        lines = content.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            # Check if this is a heading
            heading_match = re.match(r"^##\s+(?:[\U0001F300-\U0001F9FF]\s+)?(.+)$", line)

            if heading_match:
                # Save previous section if exists
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = heading_match.group(1).strip()
                current_content = []
            elif current_section:
                # Add line to current section
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def read_section(self, date: datetime, section_name: str) -> Optional[str]:
        """Read a specific section from the daily note.

        Args:
            date: Date of the note
            section_name: Name of the section (without ## or emoji)

        Returns:
            Content of that section, or None if not found
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            return None

        with open(note_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        return self._extract_section(post.content, section_name)

    def write_to_section(
        self, date: datetime, section_name: str, content: str, append: bool = False
    ) -> bool:
        """Write or append content to a specific section.

        Args:
            date: Date of the note
            section_name: Section to write to (without ## or emoji)
            content: Content to write
            append: If True, append to existing content. If False, replace.

        Returns:
            True if successful
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            return False

        with open(note_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        lines = post.content.split("\n")
        new_lines = []
        in_target_section = False
        section_found = False
        section_pattern = rf"^##\s+(?:[\U0001F300-\U0001F9FF]\s+)?{re.escape(section_name)}\s*$"

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if we're at the target section
            if re.match(section_pattern, line, re.IGNORECASE):
                new_lines.append(line)
                section_found = True
                in_target_section = True

                # Collect existing content until next section or end
                existing_content = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("## "):
                    existing_content.append(lines[i])
                    i += 1

                # Write new content
                if append:
                    # Keep existing, add new
                    new_lines.extend(existing_content)
                    if existing_content and existing_content[-1].strip():
                        new_lines.append("")  # Blank line before new content
                    new_lines.append(content)
                else:
                    # Replace with new
                    new_lines.append(content)

                in_target_section = False
                continue

            new_lines.append(line)
            i += 1

        if not section_found:
            return False

        post.content = "\n".join(new_lines)

        # Write atomically
        temp_path = note_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        temp_path.rename(note_path)

        return True

    def add_section(
        self, date: datetime, section_name: str, content: str, emoji: str = ""
    ) -> bool:
        """Add a new section to the daily note.

        Args:
            date: Date of the note
            section_name: Name for the new section
            content: Initial content
            emoji: Optional emoji prefix

        Returns:
            True if successful
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            return False

        with open(note_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Add section at end
        heading = f"## {emoji} {section_name}" if emoji else f"## {section_name}"
        new_section = f"\n\n{heading}\n{content}"

        post.content += new_section

        # Write atomically
        temp_path = note_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        temp_path.rename(note_path)

        return True
