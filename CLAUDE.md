# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Coach AI is an MCP (Model Context Protocol) server that provides ADHD-friendly productivity coaching tools. It integrates with Claude Desktop and Claude Code to provide persistent memory, task management, goal tracking, and Obsidian vault integration.

**Key Design Philosophy:**
- Combat decision paralysis with clear recommendations
- Reduce cognitive load through persistent memory
- ADHD-friendly with quick wins and momentum building
- Client-agnostic MCP server (not a standalone app)

## Development Commands

### Testing the Server

Test the MCP server interactively using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run --directory /path/to/coach-ai python -m coach_ai.server
```

This opens a web UI at http://localhost:5173 for testing tools without an AI client.

### Installation

```bash
# Clone and install
uv pip install -e .

# Or with pip
pip install -e .
```

## Architecture

### MCP Server Structure

**Entry Point:** `src/coach_ai/server.py`
- Uses FastMCP framework to expose tools
- All tools are async functions decorated with `@mcp.tool()`
- Main entry point: `main()` which runs `mcp.run(transport="stdio")`

### Core Modules

**storage.py** - Database layer
- SQLite database with aiosqlite for async operations
- Global connection via `get_db()` - creates schema on first access
- Tables: `todos`, `goals`, `user_facts`, `accomplishments`
- Database path: `data/coach.db` (configurable via `COACH_DB_PATH` env var)

**recommendations.py** - Recommendation engine
- Generates context for LLM-based recommendations
- Analyzes todos, goals, user facts, and accomplishments
- Returns formatted context string for AI to interpret
- ADHD considerations: decision paralysis, activation energy, time blindness

**obsidian.py** - Obsidian vault integration
- `ObsidianVault` class handles all file operations
- Uses `python-frontmatter` for YAML frontmatter parsing
- Atomic file writes (temp file + rename pattern)
- Extracts tasks from markdown checkboxes: `- [ ]` and `- [x]`
- Section-based navigation using `## Heading` patterns
- Supports emoji prefixes in headings (e.g., `## 🎯 Focus`)

**daily_notes.py** - Daily note orchestration
- Bridges MCP tools with ObsidianVault operations
- Smart daily note creation with carryover from yesterday
- Lazy vault initialization via `get_vault()`
- Requires `OBSIDIAN_VAULT_PATH` environment variable

### Environment Variables

Set in Claude Desktop config under `env` section:

```json
{
  "env": {
    "COACH_DB_PATH": "data/coach.db",
    "OBSIDIAN_VAULT_PATH": "/path/to/vault",
    "DAILY_NOTES_FORMAT": "Daily Notes/{date}.md"
  }
}
```

- `COACH_DB_PATH`: SQLite database location (default: `data/coach.db`)
- `OBSIDIAN_VAULT_PATH`: Absolute path to Obsidian vault root (required for Obsidian features)
- `DAILY_NOTES_FORMAT`: Daily note path template with `{date}` placeholder (default: `Daily Notes/{date}.md`)

## MCP Tool Categories

### Todo Management
- `add_todo()` - ENHANCED: Create todos with priority, auto-categorization, time extraction, quick win detection
  - New `quick` parameter for low-energy tasks
  - Auto-tags: [Sprint Work], [Management], [Deadline], [Quick Win]
  - Extracts time estimates from notes ("30min", "2h")
  - Returns task ID and guidance
- `list_todos()` - Filter by active/completed/all
- `complete_todo()` - Mark complete with timestamp
- `delete_todo()` - Permanent deletion

### Goal Management
- `set_goal()` - Goals with timeframe and category
- `list_goals()` - Active or all goals

### User Context
- `add_user_fact()` - Store user preferences/patterns/challenges
- `get_user_context()` - Retrieve stored facts
- `log_accomplishment()` - Track wins for positive reinforcement

### Recommendations
- `get_recommendation()` - Main "what should I do now?" feature
- Returns context for AI to generate personalized suggestions

### Obsidian Integration
- `start_my_day()` - ENHANCED PHASE 1: Smart task selection and daily note creation
  - Syncs yesterday's completed tasks from Obsidian checkboxes
  - Intelligently selects 3-5 tasks from backlog (critical, important, quick wins)
  - Creates daily note with selected tasks organized by priority
  - Deterministic algorithm (no LLM required)
- `sync_daily_note()` - NEW PHASE 1: Bidirectional sync from Obsidian
  - Reads markdown checkboxes (- [x]) from daily note
  - Fuzzy matches checkbox text to todos in database
  - Marks matching todos as complete with timestamp
  - Enables Obsidian-first workflow
- `create_daily_note()` - Smart population with carryover and goal-based tasks
- `sync_from_daily_note()` - Read and parse daily note (legacy)
- `read_daily_note_full()` - Complete note with all sections
- `read_daily_note_section()` - Read specific section by name
- `write_daily_note_section()` - Write/append to section
- `add_daily_note_section()` - Create new section with optional emoji
- `generate_daily_summary()` - End-of-day summary with completion stats
- `get_daily_note_path()` - Get file path for a date

## Important Patterns

### Database Schema

**Todos table** (Phase 1 enhanced):
- `status` field: "active" or "completed"
- `priority`: "low", "medium", "high"
- `skipped_count` (NEW): Tracks tasks moved forward repeatedly (backlog hell detection)
- `time_estimate` (NEW): Estimated minutes to complete
- `last_scheduled` (NEW): Last date task was scheduled in daily note

**Goals table**:
- `status` field: "active" (no completion tracking yet)

**User facts table**:
- `category`: "preferences", "challenges", "strengths", "patterns", "routines", "general"

**Schema versioning** (Phase 1):
- Migrations tracked in `schema_version` table
- Safe column additions via `migrations.py`
- Current version: 1

### Task Priority in Daily Notes

Tags embedded in task text:
- `#high-priority` or `#urgent` → high priority
- `#low-priority` → low priority
- No tag → medium priority

### Daily Note Structure

Created notes follow this structure:
- Frontmatter: date, type, day_of_week
- `## 🎯 Focus for Today` - Main and backup goals
- `## ⚡ Quick Win (Start Here)` - Smallest activation energy task
- `## ✅ Tasks` - Organized by subsections (Carried Over, From Goals, Low-Effort)
- `## 💪 Accomplishments` - Filled as tasks complete
- `## 📝 Notes` - Free-form
- `## 🧠 Coach AI Insights` - Auto-generated context

### Section Extraction Pattern

Sections match: `^##\s+(?:emoji\s+)?Section Name\s*$`
Content captured until next `##` heading or EOF
Case-insensitive matching

### Atomic File Writes

All Obsidian file operations use:
1. Write to `.tmp` file
2. Rename to actual file (atomic on POSIX)
This prevents corruption if interrupted

### ADHD-Friendly Features (Phase 1 Enhanced)

- **Smart task selection**: Deterministic algorithm picks 3-5 tasks from backlog
  - 1 critical task (deadlines or highest priority)
  - 1-2 important tasks (high-impact work)
  - 2-3 quick wins (low-effort, dopamine generators)
- **Quick wins**: Low activation energy tasks for momentum
  - Auto-detected from time estimates (<30min)
  - Can be explicitly flagged with `quick=True`
  - Shown with time estimates in daily note
- **Auto-categorization**: Keywords trigger automatic tagging
  - Sprint/Management/Deadline detection
  - Time estimate extraction from notes
- **Backlog hell prevention**: Tracks `skipped_count` for tasks moved forward 5+ times
- **Obsidian-first workflow**: Work in daily note, sync back to database
- **Friction-free capture**: Add todos with minimal decisions (defaults to medium priority)
- **Late start detection**: `datetime.now().hour > 10` triggers gentler quick wins
- **Monday awareness**: Extra-small tasks on Mondays
- **Carryover limiting**: Max 3-5 tasks selected to avoid overwhelm
- **Positive reinforcement**: Accomplishment logging and celebration

## Testing Notes

When adding new tools:
1. Define async function in appropriate module
2. Import and decorate with `@mcp.tool()` in `server.py`
3. Test with MCP Inspector before deploying
4. Ensure error messages are user-friendly and actionable

## Configuration for Claude Desktop

Example `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "coach-ai": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/coach-ai",
        "python",
        "-m",
        "coach_ai.server"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/Users/username/Documents/Vault",
        "DAILY_NOTES_FORMAT": "Daily Notes/{date}.md"
      }
    }
  }
}
```

Claude Code automatically detects MCP servers from this config file.