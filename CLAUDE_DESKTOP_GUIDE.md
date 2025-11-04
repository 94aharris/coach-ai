# Using Coach AI from Claude Desktop

## Setup Complete

Your Claude Desktop is now configured to use Coach AI. Here's what to do next:

## Step 1: Restart Claude Desktop

**IMPORTANT**: You must completely quit and restart Claude Desktop for the changes to take effect.

1. Open Claude Desktop (if not already open)
2. Press **Cmd+Q** to fully quit (don't just close the window)
3. Open Claude Desktop again

## Step 2: Verify Tools Are Loaded

After restarting, look for the **hammer icon** (🔨) at the bottom right of the chat input box. This indicates that MCP tools are loaded and ready to use.

If you don't see the hammer icon:
- Check that you fully quit and restarted Claude Desktop (not just closed the window)
- Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log`
- Verify config: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json`

## Step 3: Start Chatting!

Just talk to Claude naturally. You don't need to explicitly call tools - Claude will use them automatically when appropriate.

### First Conversation Examples

**Start Simple:**

> You: "Hi! I just set up Coach AI. Can you help me get organized?"

Claude will recognize it has access to your coaching tools and help you get started.

**Add Your First Todo:**

> You: "I need to finish my quarterly report today. Add that as a high priority todo."

Claude will call `add_todo()` automatically.

**Get a Recommendation:**

> You: "What should I focus on right now?"

Claude will call `get_recommendation()` and give you a personalized suggestion.

**Set a Goal:**

> You: "I want to launch my side project by the end of this month"

Claude will call `set_goal()` and help you break it down.

**Teach Claude About You:**

> You: "Remember that I work best in the mornings before 11am"

Claude will call `add_user_fact()` to store this.

## How It Works Behind the Scenes

When you chat with Claude:

1. **You send a message** in natural language
2. **Claude decides** if any Coach AI tools are needed
3. **Claude calls the tools** automatically (you'll see a brief "Thinking..." indicator)
4. **Claude reads the results** and incorporates them into the response
5. **You get a natural response** with the information you need

You'll sometimes see tool calls in a collapsed section you can expand to see what happened.

## Example Full Workflow

Here's a realistic morning planning session:

**You:**
> Morning! What should I tackle today?

**Claude:**
> *[Calls `list_todos()` and `list_goals()` in the background]*
>
> Good morning! Let me check your current state...
>
> You have 3 active todos:
> - High priority: Finish quarterly report
> - Medium: Review proposal
> - Low: Call dentist
>
> Your goal of "Launch side project by month-end" is coming up. Given that it's morning (your peak time based on what you've told me), I recommend starting with the quarterly report. That's your highest priority and aligns with when you focus best.
>
> Want me to break it down into smaller steps?

**You:**
> Yes please!

**Claude:**
> Here are manageable chunks for finishing the report:
>
> 1. Review your notes (10 min)
> 2. Update the data section (20 min)
> 3. Write conclusions (15 min)
> 4. Quick proofread (10 min)
>
> Start with step 1 - just 10 minutes to review your notes. Ready to begin?

**You:**
> Done! I finished the report.

**Claude:**
> *[Calls `complete_todo(1)` and `log_accomplishment()`]*
>
> Excellent work! I've marked that as complete and logged it as an accomplishment.
>
> *[Calls `get_recommendation()`]*
>
> What's next? You still have the proposal review (medium priority) and it's still morning. Want to ride that momentum?

## What Makes This Different

Unlike other todo apps or AI chats:

1. **No app switching** - Everything in one conversation
2. **Learns your patterns** - Remembers what works for you
3. **ADHD-aware** - Designed for decision paralysis and overwhelm
4. **Natural interface** - Just chat, don't think about commands
5. **Local & private** - All data stays on your machine

## Tips for Best Results

1. **Chat naturally** - Don't try to format things specially
2. **Share patterns** - Tell Claude what works/doesn't work for you
3. **Be honest** - If you're overwhelmed or stuck, say so
4. **Use it daily** - The more you use it, the better it learns
5. **Celebrate wins** - Share when you complete things

## Troubleshooting

### Tools Not Working

If Claude seems unaware of the coaching tools:

1. **Check the 🔨 icon** is visible (means tools are loaded)
2. **Ask explicitly**: "Do you have access to Coach AI tools?"
3. **Check logs**: `tail -f ~/Library/Logs/Claude/mcp*.log`
4. **Restart again**: Sometimes takes 2 restarts

### Database Issues

Your data is stored in `<coach-ai-directory>/data/coach.db`

To backup:
```bash
cp <coach-ai-directory>/data/coach.db ~/Desktop/coach_backup.db
```

To reset (if corrupted):
```bash
rm <coach-ai-directory>/data/coach.db
```

The database will be recreated automatically on next use.

### Server Errors

Test the server directly:
```bash
cd <coach-ai-directory>
uv run python -m coach_ai.server
```

Replace `<coach-ai-directory>` with your installation path. Should show no errors. Press Ctrl+C to stop.

## Advanced: Using with Claude Code

Coach AI also works with Claude Code (this interface you're using now)! Claude Code automatically detects MCP servers from Claude Desktop's config.

Just chat in Claude Code and ask about your todos, goals, etc. Same commands work here.

## What's Next?

Once you're comfortable with the basics:

1. **Daily planning** - Start each day with "What should I focus on today?"
2. **Weekly reviews** - Ask Claude to help review your week
3. **Goal tracking** - Set medium and long-term goals
4. **Pattern recognition** - Let Claude learn what works for you
5. **Obsidian integration** - (Coming in Phase 2) Sync with your notes

## Questions?

Just ask Claude! Try:
- "Show me all available Coach AI tools"
- "What can you help me with using Coach AI?"
- "Give me examples of how to use the coaching tools"

Enjoy your new ADHD coaching assistant!
