# Coach AI - Quick Start Guide

## What You Just Built

Coach AI is an **MCP (Model Context Protocol) server** that provides ADHD coaching tools to any AI chat interface. It's NOT a standalone chat app - instead, it plugs into Claude Desktop, Claude Code, or any MCP-compatible client.

## How It Works

1. **Coach AI runs as a background service** when you use Claude Desktop
2. **Claude can call your tools** automatically during conversations
3. **Your data persists** in a local SQLite database
4. **Works everywhere** - Claude Desktop, Claude Code, LibreChat, etc.

## Setup (2 minutes)

### Step 1: Copy Configuration to Claude Desktop

```bash
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Important**: If you already have MCP servers configured, you'll need to merge the config manually. Open the file and add coach-ai to the existing `mcpServers` section.

### Step 2: Restart Claude Desktop

Completely quit Claude Desktop (Cmd+Q) and reopen it.

### Step 3: Verify It's Working

Look for the 🔨 (hammer) icon in the chat input box. This indicates MCP tools are loaded.

## Using Coach AI

Just chat naturally with Claude! Here are some things to try:

### Get Started
> "What should I focus on right now?"

Claude will call `get_recommendation()` and give you a personalized suggestion.

### Add Todos
> "Add a high priority todo to finish the quarterly report"
> "Add a todo: call the dentist, low priority"

Claude calls `add_todo()` with the right parameters.

### View Your Todos
> "Show me my active todos"
> "What's on my list?"

Claude calls `list_todos()` to show your tasks.

### Complete Todos
> "Mark todo #3 as complete"
> "I finished the report"

Claude calls `complete_todo()` or `log_accomplishment()`.

### Set Goals
> "I want to launch my side project by the end of this month"
> "Set a goal: exercise 3x per week, this is a health goal"

Claude calls `set_goal()`.

### Help Claude Learn About You
> "Remember that I work best in the mornings"
> "I get overwhelmed when I have more than 3 high-priority tasks"
> "Note that I struggle with context switching"

Claude calls `add_user_fact()` to remember important patterns.

### View Your Context
> "What do you know about me?"
> "Show me my goals"

Claude calls `get_user_context()` and `list_goals()`.

## Testing Without Claude Desktop

You can test the server directly with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run --directory /path/to/coach-ai python -m coach_ai.server
```

Replace `/path/to/coach-ai` with your installation directory. This opens a web interface where you can test each tool manually.

## Database Location

All your data is stored in `data/coach.db`. This file is created automatically the first time you use Coach AI.

To back up your data:
```bash
cp data/coach.db data/coach_backup_$(date +%Y%m%d).db
```

## Available Tools

**Todo Management:**
- `add_todo(title, priority, notes)` - Add a new todo
- `list_todos(status)` - List todos (active/completed/all)
- `complete_todo(todo_id)` - Mark complete
- `delete_todo(todo_id)` - Delete permanently

**Goal Management:**
- `set_goal(goal, timeframe, category)` - Set a new goal
- `list_goals(status)` - List all goals

**Learning & Context:**
- `add_user_fact(fact, category)` - Remember something about you
- `get_user_context()` - Retrieve what Coach knows about you
- `log_accomplishment(description)` - Log a win

**Recommendations:**
- `get_recommendation()` - Get a personalized "what should I do now?" suggestion

## Troubleshooting

### Tools Not Showing Up (No Hammer Icon)

1. Check that Claude Desktop config is correct:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Make sure the path in the config matches your actual coach-ai directory

3. Restart Claude Desktop completely (Cmd+Q, then reopen)

4. Check Claude Desktop logs:
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

### Server Crashes or Errors

Test the server directly:
```bash
uv run python -m coach_ai.server
```

This will show any Python errors.

### Database Issues

If you need to reset your database:
```bash
rm data/coach.db
```

It will be recreated automatically.

## What's Next?

You now have a working ADHD coaching assistant! Here are ideas for next steps:

1. **Use it daily** - Let Claude learn your patterns
2. **Obsidian integration** - Add tools to read your daily notes (Phase 2)
3. **Enhanced recommendations** - Add time-of-day awareness
4. **Task breakdown** - Automatically split overwhelming tasks
5. **Weekly reviews** - Add prompt templates for reflection

## Philosophy

Coach AI is designed for ADHD:
- **Reduces decision paralysis** by giving clear recommendations
- **Remembers patterns** so you don't have to explain yourself repeatedly
- **Celebrates wins** to provide dopamine hits
- **Stays simple** to avoid overwhelming complexity
- **Works everywhere** - not tied to one interface

Enjoy your new AI coach!
