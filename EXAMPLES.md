# Coach AI - Example Conversations

This guide demonstrates realistic conversations with Coach AI to help you understand how to interact with it effectively. The examples show how natural conversation triggers the appropriate tools automatically.

**Note:** Tool calls shown in *[brackets]* are for illustration - in actual use, these happen automatically in the background.

## First Time Setup

**You:**
> Hi! I'm setting up an ADHD coaching system. Can you help me get started?

**Claude (using Coach AI):**
> I'd love to help! I have access to tools that let me track todos, goals, and learn about your patterns. Let me start by understanding your context.
>
> What are some of the main challenges you face with ADHD? For example, do you struggle with:
> - Decision paralysis when faced with multiple tasks?
> - Hyperfocus that makes you forget breaks?
> - Time blindness?
> - Starting tasks (activation energy)?

**You:**
> Yes to all of those! Especially decision paralysis. I also work best in the mornings.

**Claude:**
> *[Calls `add_user_fact("Experiences decision paralysis frequently", "challenges")`]*
> *[Calls `add_user_fact("Hyperfocus can make them forget breaks", "challenges")`]*
> *[Calls `add_user_fact("Works best in the mornings", "patterns")`]*
>
> Got it! I've noted those patterns. Let's start simple. What are 2-3 things you need to get done today?

## Daily Planning

**You:**
> I need to finish a report, review a proposal, and call my dentist.

**Claude:**
> *[Calls `add_todo("Finish report", "high", "")`]*
> *[Calls `add_todo("Review proposal", "medium", "")`]*
> *[Calls `add_todo("Call dentist", "low", "")`]*
>
> I've added those to your list:
> - High priority: Finish report
> - Medium priority: Review proposal
> - Low priority: Call dentist
>
> Since you mentioned you work best in mornings and it's [checks time], I recommend starting with the report. That's your highest priority and matches your peak energy time.
>
> Want me to break down the report task into smaller steps to make it less overwhelming?

**You:**
> Yes please!

**Claude:**
> Based on what finishing a report typically involves, here are manageable 20-minute chunks:
>
> 1. Gather all your notes/data (10 min)
> 2. Create a quick outline (15 min)
> 3. Draft the introduction (20 min)
> 4. Fill in the main sections (30 min - can split into smaller pieces)
> 5. Write conclusion (15 min)
> 6. One quick proofread (10 min)
>
> Which step are you on? Or should we start with step 1?

## Getting Unstuck

**You:**
> I'm staring at my todo list and I can't decide what to do. Help!

**Claude:**
> *[Calls `get_recommendation()`]*
>
> Let me check your current state...
>
> You have 5 active todos:
> - High priority: Finish report
> - Medium: Review proposal
> - Medium: Update project docs
> - Low: Call dentist
> - Low: Organize files
>
> Based on what I know about you:
> - It's morning (your best time)
> - You have 2 high/medium tasks
> - You mentioned you work best with clear priorities
>
> **My recommendation: Start with the report.**
>
> This is your highest priority, and you're in your peak morning hours. The other tasks can wait until after lunch.
>
> First concrete step: Just open the report file. That's it. Lower the activation energy by committing to only one tiny action.
>
> Sound doable?

## Logging Accomplishments

**You:**
> I finished the report!

**Claude:**
> *[Calls `complete_todo(1)`]*
> *[Calls `log_accomplishment("Finished report")`]*
>
> Amazing work! That was your highest priority task and you knocked it out during your peak hours. That's excellent self-awareness in action.
>
> *[Calls `get_recommendation()`]*
>
> What's next? You have some medium-priority items. How's your energy level right now?

**You:**
> Pretty good! I'm feeling productive.

**Claude:**
> Perfect! Since you're in flow, let's ride that momentum. Next up: Review the proposal. This should take about 20-30 minutes based on typical review tasks.
>
> But remember - set a timer so you don't hyperfocus and forget to take a break. Want me to remind you in 30 minutes?

## Setting Goals

**You:**
> I want to launch my side project by the end of this month.

**Claude:**
> *[Calls `set_goal("Launch side project", "end of this month", "career")`]*
>
> Great goal! I've noted it. Let's break this down into milestones:
>
> 1. What's left to do before you can launch?
> 2. Which pieces are blockers vs nice-to-haves?
> 3. How much time can you realistically dedicate each week?
>
> Let's create a realistic plan that accounts for your ADHD patterns.

**You:**
> I need to finish the landing page, set up payments, and write some docs. I can probably do 5 hours a week.

**Claude:**
> *[Calls `add_todo("Finish landing page", "high", "For side project launch")`]*
> *[Calls `add_todo("Set up payment processing", "high", "For side project launch")`]*
> *[Calls `add_todo("Write project documentation", "medium", "For side project launch")`]*
>
> Added those as todos linked to your goal. With 5 hours/week and 4 weeks left, you have about 20 hours total.
>
> Landing page: ~6 hours
> Payments: ~8 hours (can be tricky)
> Docs: ~4 hours
>
> That's 18 hours - tight but doable with a 2-hour buffer. Key will be scheduling specific blocks. When this week works best for you?

## Learning About You

**You:**
> I realized I can never focus after 3pm. My brain is done for the day.

**Claude:**
> *[Calls `add_user_fact("Brain is done after 3pm, cannot focus on complex tasks", "patterns")`]*
>
> That's really valuable self-knowledge! I've noted that. This means:
>
> - Morning (before 3pm): Complex, high-priority tasks
> - After 3pm: Low-stakes tasks like organizing, simple emails, planning
>
> Looking at your todo list, that dentist call and file organization would be perfect after-3pm tasks. I'll keep this in mind for future recommendations.

## Weekly Review

**You:**
> Can we do a weekly review?

**Claude:**
> *[Calls `list_goals()`]*
> *[Calls `get_user_context()`]*
> *[Calls accomplishment query]*
>
> Absolutely! Let's look at your week:
>
> **Accomplishments:**
> - Finished quarterly report
> - Reviewed marketing proposal
> - Made dentist appointment
> - Completed 2 side project tasks
>
> **Active Goals:**
> - Launch side project (end of month) - ON TRACK
> - Exercise 3x/week (ongoing) - need to check in
>
> **Patterns I've noticed:**
> - You completed 4 high-priority tasks
> - All were done in morning hours (your peak time)
> - You struggled on days with 4+ todos (decision paralysis)
>
> **Recommendations for next week:**
> - Keep limiting yourself to 3 tasks per day max
> - Block morning time for side project work
> - Add low-stakes tasks for after 3pm
>
> How does this feel? Anything you want to adjust?

## Handling Overwhelm

**You:**
> I have 15 things on my list and I'm freaking out.

**Claude:**
> *[Calls `list_todos()`]*
>
> Okay, I see the list. Let's triage together. First, breathe. We're going to break this down.
>
> *[Calls `add_user_fact("Gets overwhelmed with long todo lists", "challenges")`]*
>
> Of these 15 items:
> - How many are actually urgent (need to happen today/tomorrow)?
> - How many can wait until next week?
> - How many can be delegated or dropped?
>
> Let's identify your TRUE priorities first. Give me the top 3 that absolutely must happen.

**You:**
> Finish client presentation, respond to urgent email, and prep for tomorrow's meeting.

**Claude:**
> Good. Those are your only priorities for TODAY. Everything else waits.
>
> I'm going to suggest we mark the other 12 as low priority or move them to a "later" list. Having 15 active todos is triggering your decision paralysis. Let's keep your active list under 5 items always.
>
> Sound good?

## Integration Examples

These examples show how Coach AI works seamlessly in conversation without needing to explicitly "use tools":

**Natural Todo Creation:**
> You: "Oh, I should also email Sarah about the project"
> Claude: *[Calls `add_todo("Email Sarah about project", "medium", "")`]* Added that to your list!

**Context-Aware Responses:**
> You: "What should I work on?"
> Claude: *[Calls `get_recommendation()` which retrieves user facts]* Given that it's 10am (your best time) and you mentioned you struggle with context switching, I recommend finishing that client presentation you started yesterday. Switching to something new right now would cost you mental energy.

**Automatic Learning:**
> You: "I always get distracted when I work from the couch"
> Claude: *[Calls `add_user_fact("Gets distracted working from couch", "patterns")`]* Good to know! I'll remember that. Where do you focus best?

## Tips for Best Results

1. **Be conversational** - Don't think about the tools, just chat naturally
2. **Share patterns** - Mention when you notice what works or doesn't work
3. **Use it daily** - The more you use it, the better it learns your patterns
4. **Be honest** - If you're overwhelmed, struggling, or avoiding something, say so
5. **Celebrate wins** - Share when you complete things so they get logged

Coach AI is designed to feel like a conversation with a coach who remembers everything about you and helps you navigate ADHD challenges. Treat it like a real coaching relationship!
