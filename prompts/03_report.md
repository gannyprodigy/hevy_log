# Step 3: Deep Analysis Report — Part 1 (Sections 1–4)

Write a file named `report_YYYY-MM-DD.txt` (today's date) using the Write tool.
**This step writes the first half only.** A follow-up step will append sections 5–8.

Every claim must reference actual numbers from the log.

---

## User Profile
- **Name:** Ganesh | 44M | 181cm | 87kg -> 79kg goal
- **Goal:** Body recomposition — lose fat, preserve/build muscle
- **Target pace:** 0.5kg/week fat loss at ~15% calorie deficit
- **Training frequency target:** 5 sessions/week
- **Deload:** Every 4 weeks (reduce to 2 sets per exercise, same weight)

---

## Step 3a — Load previous report for comparison

Before writing, check for existing `report_*.txt` files (excluding today's):

```bash
ls -t report_*.txt 2>/dev/null | grep -v "$(date +%Y-%m-%d)" | head -1
```

If one exists, read it and extract these baselines:
- Volume per muscle group (30-day totals)
- Best e1RM per exercise
- Session count and adherence %
- Push/pull ratio
- Rear delt and trap set counts

Use these as **comparison baselines** throughout, showing deltas (up/down/stable) vs the current period.
If no previous report exists, note "First report — no baseline" and proceed.

---

## Write sections 1–4 to the file

### 1. EXECUTIVE SUMMARY
2–3 sentences. Overall training health score (1–10). Biggest win. Biggest risk.
If a previous report exists, state whether this period is better or worse overall.

### 2. WEEK-BY-WEEK BREAKDOWN
For each of the 4 weeks in the 30-day period:
- Sessions completed vs 5 target
- Total volume (kg x reps)
- Volume change % vs prior week
- Notable events (missed days, PRs, deload)

Include a simple ASCII volume trend chart using only plain characters (no box-drawing).

### 3. STRENGTH PERFORMANCE
For every exercise in the log:
- Best estimated 1RM this period
- vs previous report baseline: improved / stable / declined (with kg delta)
- Sets x reps x weight logged
- Flag if stalled (same weight 3+ sessions)
- Flag new PRs

Group by: Compound lifts first, then isolation.

### 4. MUSCLE GROUP BALANCE
Plain text table (use spaces and dashes, not box-drawing characters):

  Muscle Group    | Sets(30d) | Sets/Wk | Target/Wk | vs Prev | Status
  ----------------+-----------+---------+-----------+---------+--------
  ...

Priority flags:
- Rear delts: target 8+ sets/week — below = rotator cuff imbalance risk
- Traps: target 6+ sets/week
- Push/Pull ratio: target >= 1.0 — below = shoulder impingement risk

---

## Tone
Clinical, specific, evidence-informed. Coach reviewing real data — not a generic chatbot.
