# Obsidian Integration Setup Guide

Coach AI now integrates with Obsidian to provide seamless daily note management!

## What This Adds

✅ **Auto-create daily notes** - Coach AI creates your daily note with smart population
✅ **Bi-directional sync** - Read from and write to your daily notes
✅ **Smart task carrying** - Incomplete tasks from yesterday automatically carry over
✅ **Goal integration** - Tasks based on your active goals
✅ **Low-motivation support** - Extra-small "quick win" tasks when you need them
✅ **Zero manual syncing** - Everything happens automatically

## Setup Instructions

### Step 1: Find Your Obsidian Vault Path

Your Obsidian vault is the folder that contains your notes. To find it:

1. Open Obsidian
2. Click the vault switcher (folder icon in bottom left)
3. Click "Manage vaults"
4. Find your vault and note the path

Common locations:
- macOS: `/Users/your-username/Documents/ObsidianVault`
- Windows: `C:\Users\your-username\Documents\ObsidianVault`
- Linux: `/home/your-username/Documents/ObsidianVault`

### Step 2: Configure Claude Desktop

Edit your Claude Desktop config file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Add the `env` section** to your coach-ai server config:

```json
{
  "mcpServers": {
    "coach-ai": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/harrisal/coach-ai",
        "python",
        "-m",
        "coach_ai.server"
      ],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/Users/your-username/Documents/ObsidianVault",
        "DAILY_NOTES_FORMAT": "Daily Notes/{date}.md"
      }
    }
  }
}
```

**Important:** Replace `/Users/your-username/Documents/ObsidianVault` with YOUR actual vault path!

### Step 3: Configure Daily Notes Format (Optional)

If your daily notes are in a different location, adjust `DAILY_NOTES_FORMAT`:

- Default: `"Daily Notes/{date}.md"` → creates notes at `Daily Notes/2025-11-04.md`
- Root level: `"{date}.md"` → creates notes at `2025-11-04.md`
- Custom folder: `"Journal/{date}.md"` → creates notes at `Journal/2025-11-04.md`

The `{date}` placeholder is replaced with `YYYY-MM-DD` format.

### Step 4: Restart Claude Desktop

After updating the config:
1. Quit Claude Desktop completely (Cmd+Q or Ctrl+Q)
2. Reopen Claude Desktop
3. The Obsidian integration is now active!

## Usage

### Create Your Daily Note

Just ask Claude:
> "Create my daily note"

Coach AI will:
- Create today's daily note in your vault
- Pull in incomplete tasks from yesterday
- Add tasks based on your goals
- Include a "quick win" for easy starting
- Add insights and context

### Read Your Daily Note

Ask Claude:
> "What's in my daily note?"
> "Show me today's tasks"

Coach AI will read and summarize your daily note.

### Get the Daily Note Path

> "Where is my daily note?"

Returns the file path so you can open it in Obsidian.

### Automatic Integration

The best part: **You don't need to ask!**

When you say things like:
- "What should I focus on today?"
- "Add a todo..."
- "What's my plan?"

Coach AI automatically checks if your daily note exists, and creates it if needed!

## Daily Note Format

Coach AI creates notes with this structure:

```markdown
---
date: 2025-11-04
type: daily-note
day_of_week: monday
---

# Monday, November 4, 2025

## 🎯 Focus for Today
**Main Goal:** [Generated based on your goals and yesterday]
**Backup Goal:** [Alternative if main goal is blocked]

## ⚡ Quick Win (Start Here)
- [ ] [Smallest possible task to build momentum]

## ✅ Tasks
### Carried Over from Yesterday
- [ ] [Tasks you didn't finish]

### From Your Goals
- [ ] [Tasks aligned with active goals]

### Low-Effort Tasks
- [ ] [Easy tasks for low-energy moments]

## 💪 Accomplishments
[Filled in as you complete things]

## 📝 Notes
[Your free-form notes]

## 🧠 Coach AI Insights
Created: 9:45am
[Context about why these tasks were chosen]
[Patterns Coach AI has noticed]
```

## Example Workflow

**Morning (Low Motivation Day):**

> You: "I'm struggling to get started"

> Claude:
> *[Checks if daily note exists - it doesn't]*
> *[Creates daily note with extra-small quick win]*
>
> I've got you. I created your daily note with ONE tiny task:
> Open your Obsidian vault and look at the note. That's it.
>
> Your daily note is at: Daily Notes/2025-11-04.md
>
> Do that one thing, then come back.

**Mid-Day:**

> You: "Add a todo to review the proposal"

> Claude:
> *[Reads daily note]*
> *[Adds task to daily note]*
> *[Updates daily note file]*
>
> Added to your daily note: "Review the proposal"
>
> You now have 4 active tasks today.

**Evening:**

> You: "How did today go?"

> Claude:
> *[Reads daily note]*
> *[Analyzes accomplishments]*
>
> Great day! You completed 3 out of 4 tasks:
> ✅ Report finished
> ✅ Proposal reviewed
> ✅ Dentist called
>
> I've updated your daily note with these accomplishments.

## Troubleshooting

### "Obsidian vault not configured"

Make sure:
1. `OBSIDIAN_VAULT_PATH` is set in your Claude Desktop config
2. The path points to an existing folder
3. You restarted Claude Desktop after changing config

### "Daily note not found"

Coach AI will offer to create it! Just say "yes" or "create my daily note".

### Daily note in wrong location

Check your `DAILY_NOTES_FORMAT` setting. Make sure:
- The folder exists in your vault (e.g., `Daily Notes/`)
- The format uses `{date}` placeholder
- The path is relative to vault root

### Changes not appearing in Obsidian

Coach AI writes files atomically and safely. If you have Obsidian open:
1. It should auto-refresh when files change
2. If not, switch to another note and back
3. Or close and reopen the note

## Benefits

### For ADHD

✅ **Removes activation energy** - No blank page paralysis
✅ **Reduces decisions** - Coach AI picks what to work on
✅ **Builds momentum** - Quick wins create dopamine
✅ **Zero manual work** - Syncing happens automatically
✅ **Context preservation** - Your patterns are remembered

### For Productivity

✅ **Single source of truth** - Daily note has everything
✅ **Portable** - Markdown travels with your vault
✅ **Version controlled** - Works with git/sync
✅ **Human readable** - Can edit manually anytime
✅ **Works offline** - Just local file operations

## Next Steps

1. Set up the vault path (Steps 1-4 above)
2. Restart Claude Desktop
3. Ask Claude to create your daily note
4. Watch the magic happen!

Questions? Just ask Claude: "How do I use the Obsidian integration?"
