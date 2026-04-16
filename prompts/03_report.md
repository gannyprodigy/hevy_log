# Step 3: Deep Analysis Report

Write a file named `report_YYYY-MM-DD.txt` (today's date) using the Write tool.

This is the full research-grade analysis Ganesh reads in depth. Be thorough, specific, and data-driven. Every claim must reference actual numbers from the log.

---

## User Profile
- **Name:** Ganesh | 44M | 181cm | 87kg → 79kg goal
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

Use these as **comparison baselines** throughout the report, showing deltas (↑/↓/→) vs the current period. If no previous report exists, note "First report — no baseline" and proceed.

---

## Required Sections

### 1. EXECUTIVE SUMMARY
2–3 sentences. Overall training health score (1–10). Biggest win. Biggest risk. If a previous report exists, state whether this period is better or worse overall.

### 2. WEEK-BY-WEEK BREAKDOWN
For each of the 4 weeks in the 30-day period:
- Sessions completed vs 5 target
- Total volume (kg·reps)
- Volume change % vs prior week (↑/↓)
- Notable events (missed days, PRs, deload)

Include a simple ASCII volume trend chart.

If a previous report exists, show how the 30-day total compares to the prior 30-day total.

### 3. STRENGTH PERFORMANCE
For every exercise in the log:
- Best e1RM this period
- vs previous report baseline: ↑ improved / → stable / ↓ declined (with kg delta)
- Sets × reps × weight logged
- Flag if stalled (same weight 3+ sessions)
- Flag new PRs

Group by: Compound lifts first, then isolation.

### 4. MUSCLE GROUP BALANCE
| Muscle Group | Sets (30d) | Sets/Week avg | Target/Week | vs Prev | Status |
|---|---|---|---|---|---|

Priority flags:
- **Rear delts:** target 8+ sets/week — below = rotator cuff imbalance risk
- **Traps:** target 6+ sets/week
- **Push/Pull ratio:** target ≥ 1.0 — below = shoulder impingement risk

Note if any imbalance improved or worsened vs previous report.

### 5. RECOVERY & CONSISTENCY
- Total sessions vs 20 target — adherence %
- vs previous period adherence (if available)
- Average days between sessions
- Longest gap (flag if >3 days)
- Late-night sessions (after midnight) — recovery risk for 44M
- Back-to-back days with shared muscle group — flag the specific overlap

### 6. RECOMP PROGRESS ANALYSIS
- At 0.5kg/week pace: expected 2.0kg lost in 30 days
- Calorie targets: TDEE ≈ 87 × 32 = 2,784 kcal → deficit target 2,367 kcal/day (−417 kcal)
- Protein target: 174g/day (2g/kg)
- Volume adequacy for muscle retention under deficit
- Deload status: weeks since last deload, next deload due in week X

### 7. RESEARCH INSIGHTS
For Ganesh's profile (44M, recomp, posterior chain focus):
- Age-specific recovery (48–72h between same-muscle sessions)
- Best lifts for his strength-to-injury-risk profile
- Rear delt / trap priority: posture and shoulder health context
- MEV vs MRV zone for each muscle group
- Technique or programming red flags from session data
- If prior report exists: is the overall trajectory positive?

### 8. NEXT WEEK PLAN
- Sessions to prioritize
- Exercises to add or increase
- Weight/rep adjustments based on progression logic
- Deload recommendation if applicable

---

## Tone
Clinical, specific, evidence-informed. Coach reviewing real data — not a generic chatbot.
