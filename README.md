# Coach AI

A productivity coaching assistant built as an [MCP](https://modelcontextprotocol.io) (Model Context Protocol) server, designed with ADHD support in mind. Coach AI provides intelligent task management, goal tracking, and personalized recommendations through a set of tools that integrate seamlessly with any MCP-compatible AI client.

Rather than being a standalone application, Coach AI acts as a plugin that enhances your existing AI workflow with persistent memory and specialized coaching capabilities.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Development](#development)
- [Design Philosophy](#design-philosophy)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Todo Management**: Add, list, complete, and prioritize tasks
- **Goal Tracking**: Set and monitor short-term and long-term goals
- **Personalized Recommendations**: Get intelligent suggestions for what to do next based on your context
- **Learning System**: Remembers your preferences, patterns, and what works for you
- **Accomplishment Logging**: Track your wins for positive reinforcement
- **Decision Paralysis Support**: Designed specifically to help with ADHD challenges

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install Coach AI

Clone the repository and install the package:

```bash
git clone <your-repo-url>
cd coach-ai
uv pip install -e .
```

Or with pip:
```bash
pip install -e .
```

## Configuration

### For Claude Desktop

1. Open your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add Coach AI to the `mcpServers` section:

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
      ]
    }
  }
}
```

**Note**: Replace `/absolute/path/to/coach-ai` with the actual path where you cloned this repository.

3. Restart Claude Desktop completely (Quit and reopen)

4. Look for the 🔨 icon in the chat input to verify the tools are loaded

### For Claude Code

Claude Code automatically detects MCP servers configured in Claude Desktop's config file. Once you've configured the server for Claude Desktop, it will be available in Claude Code without additional setup.

## Usage

Once configured, simply chat with Claude naturally. The AI will automatically use Coach AI's tools when appropriate.

### Example Interactions

**Get a personalized recommendation:**
```
You: "What should I focus on right now?"
```
The AI will call `get_recommendation()` and provide a personalized suggestion based on your todos, goals, and learned preferences.

**Add a task:**
```
You: "Add a todo: Review the marketing proposal, make it high priority"
```
The AI will call `add_todo(title="Review the marketing proposal", priority="high")`.

**Set a goal:**
```
You: "I want to launch my side project by the end of this month"
```
The AI will call `set_goal(goal="Launch side project", timeframe="this month", category="career")`.

**Store context about yourself:**
```
You: "Remember that I work best in the mornings before 11am"
```
The AI will call `add_user_fact(fact="Works best in mornings before 11am", category="patterns")`.

## Available Tools

### Todo Management
- `add_todo(title, priority="medium", notes="")` - Add a new todo
- `list_todos(status="active")` - List todos (active/completed/all)
- `complete_todo(todo_id)` - Mark a todo complete
- `delete_todo(todo_id)` - Delete a todo

### Goal Management
- `set_goal(goal, timeframe, category="general")` - Set a new goal
- `list_goals(status="active")` - List all goals

### User Context
- `add_user_fact(fact, category="general")` - Remember something about you
- `get_user_context()` - Retrieve stored facts about you
- `log_accomplishment(description)` - Log something you accomplished

### Recommendations
- `get_recommendation()` - Get a personalized "what should I do now?" recommendation

## Development

### Testing with MCP Inspector

During development, you can test the server interactively:

```bash
npx @modelcontextprotocol/inspector uv run --directory /path/to/coach-ai python -m coach_ai.server
```

Replace `/path/to/coach-ai` with your installation directory. This opens a web UI at http://localhost:5173 where you can test tools without an AI client.

### Database Location

By default, Coach AI stores data in `data/coach.db`. You can customize this with the `COACH_DB_PATH` environment variable:

```bash
export COACH_DB_PATH=/path/to/custom/coach.db
```

### Project Structure

```
coach-ai/
├── src/
│   └── coach_ai/
│       ├── __init__.py
│       └── server.py       # Main MCP server implementation
├── data/
│   └── coach.db           # SQLite database (auto-created)
├── pyproject.toml
└── README.md
```

## Roadmap

- [x] Core todo management
- [x] Goal tracking
- [x] User context learning
- [x] Recommendation engine
- [ ] Obsidian vault integration (read daily notes)
- [ ] Time-of-day awareness for recommendations
- [ ] Task breakdown for overwhelming todos
- [ ] Weekly review prompts
- [ ] Energy level tracking
- [ ] Habit tracking

## Design Philosophy

Coach AI is designed with ADHD-friendly principles:

- **Combat decision paralysis**: Provides clear, actionable recommendations instead of overwhelming you with choices
- **Persistent memory**: Learns your patterns and preferences to reduce cognitive load
- **Positive reinforcement**: Celebrates accomplishments to maintain motivation
- **Simple yet extensible**: Starts with core functionality and grows with your needs
- **Client-agnostic**: Works with any MCP-compatible AI client, not tied to a specific interface

## License

MIT

## Contributing

Contributions are welcome! If you have ideas for improvements or encounter any issues, please feel free to:

- Open an issue to report bugs or suggest features
- Submit a pull request with improvements
- Share feedback on how Coach AI works for your workflow
