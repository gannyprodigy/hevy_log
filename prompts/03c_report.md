# TASK 4 OF 7: Append report sections 5 and 6

## STRICT RULES FOR THIS TASK
- Do THIS TASK ONLY. Append sections 5 and 6 only. Do not write sections 7-8.
- When done, STOP. The next task will be sent automatically.

---

# Report — Sections 5 and 6 (Recovery + Recomp)

Append sections 5 and 6 to the existing `report_YYYY-MM-DD.txt` (today's date).
Do NOT overwrite — append only.

```bash
ls -t report_*.txt | grep "$(date +%Y-%m-%d)" | head -1
```

Use plain ASCII only. Focus on this week. All times in IST.

---

## Append ONLY sections 5 and 6

### 5. REST AND RECOVERY THIS WEEK
- Sessions this week vs 5 target (and vs prior weeks in the 30-day log)
- Time between sessions — flag if less than 24h between sessions hitting the same muscle group
- Any sessions after midnight IST — explain in plain terms why this matters for fat loss and muscle retention at age 44 (cortisol, sleep, growth hormone)
- Any back-to-back sessions where the same muscle group was trained — name the exact overlap

### 6. BODY RECOMPOSITION CHECK
Plain and practical — no formulas, just key numbers:
- Daily calorie target: 2,367 kcal (deficit of 417 from estimated TDEE of 2,784)
- Protein target: 174g/day (about 2g per kg bodyweight) — and why protein is non-negotiable during a cut
- At the current training frequency this week, are muscles getting enough stimulus to hold onto during a calorie deficit? State which muscle groups are at risk of loss
- Next deload: count active training weeks and state when the deload week should happen (deload = cut sets in half, keep weights the same)

---

Append using Bash heredoc or Python append mode.
