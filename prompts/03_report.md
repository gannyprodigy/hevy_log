# Step 3: Weekly Training Report — Part 1 (Sections 1–4)

Write a file named `report_YYYY-MM-DD.txt` (today's date) using the Write tool.
**This step writes the first half only.** A follow-up step will append sections 5–8.

## IMPORTANT: Report scope
- The log covers **30 days** of data — use this for context, trends, and comparison.
- The **report itself must focus on the current week** (the 7 days ending today).
- 30-day data is background only: use it to show progress vs prior weeks and set baselines.
- Every number you quote must be from the actual log.
- All session times in the log are already in IST — display them as-is.

---

## User Profile
- Ganesh | 44M | 181cm | 87kg -> 79kg goal
- Goal: Body recomposition — lose fat, build/keep muscle
- Target: 0.5kg/week fat loss, 15% calorie deficit, 5 sessions/week
- Deload: Every 4 weeks (cut to 2 sets per exercise, same weight)

---

## Step 3a — Load previous report for comparison

Check for an existing `report_*.txt` (excluding today's):

```bash
ls -t report_*.txt 2>/dev/null | grep -v "$(date +%Y-%m-%d)" | head -1
```

If found, read it and note: volume per muscle group, best e1RM per exercise, session count, push/pull ratio, rear delt and trap sets.
Use these as comparison points — show whether things improved, stayed the same, or got worse.
If no previous report exists, write "First report — no baseline" and continue.

---

## Write sections 1–4

### 1. THIS WEEK AT A GLANCE
- Sessions this week vs 5 target, and how that compares to prior weeks in the 30-day window
- Overall score (1-10) with one sentence explaining it
- Biggest win this week (specific exercise, weight, reps)
- Biggest concern (specific, with numbers)
- One line: better, worse, or same as last report?

### 2. THIS WEEK SESSION BY SESSION
For each session this week:
- Date and time (IST), session name, duration
- Total volume (kg x reps) and sets
- Top 2-3 exercises — what weight/reps, any progress vs the prior session in the log
- Any flags (too late at night, back-to-back with same muscle group, overlapping timestamps)

Then a simple 4-week volume trend in plain text (no special characters):

  Week 1 (dates): [####    ] Xkg total, N sessions
  Week 2 (dates): [########] Xkg total, N sessions
  ...

### 3. STRENGTH: HOW ARE THE LIFTS MOVING?
For every exercise that appeared this week:
- Best weight x reps this week
- Best estimated 1-rep max (e1RM = weight x (1 + reps/30))
- Compared to the last time this exercise appeared in the 30-day log: up / same / down, and by how much
- What to do next session (specific weight and reps)
- Any flags: rep collapse, weight drop mid-session, bodyweight exercise with no load logged

Group: main lifts first (rows, presses, deadlifts, squats), then smaller exercises.

### 4. ARE THE RIGHT MUSCLES GETTING ENOUGH WORK?
Plain text table for this week's sets per muscle group:

  Muscle Group    | Sets this wk | Target/wk | Gap    | Status
  ----------------+--------------+-----------+--------+--------
  ...

Explain in plain terms:
- Which muscles got enough work (and what "enough" means)
- Which are falling short and why it matters in simple language
- Flag rear delts (need 8+ sets/week — affects shoulder health) and traps (6+ sets/week)
- Push vs pull set count and whether they're balanced

---

## Tone
Plain English. Write like a knowledgeable coach talking to someone who trains regularly but isn't a sports scientist. Explain any technical terms briefly in brackets. Specific numbers always.
