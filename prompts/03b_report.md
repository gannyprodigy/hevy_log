# Step 3b: Deep Analysis Report — Part 2 (Sections 5–8)

**Append** sections 5–8 to the existing `report_YYYY-MM-DD.txt` (today's date).
Do NOT overwrite the file — open it in append mode (Python: `open(path, "a")`).
Use the Write tool only if appending is not possible; otherwise use Bash.

```bash
REPORT=$(ls -t report_*.txt | grep "$(date +%Y-%m-%d)" | head -1)
```

Every claim must reference actual numbers from the log. Use plain ASCII only — no Unicode arrows or box-drawing characters. Use -> instead of ->, up/down/stable instead of arrows, +/- instead of +/-.

---

## Append sections 5–8

### 5. RECOVERY & CONSISTENCY
- Total sessions vs 20 target — adherence %
- vs previous period adherence (if available)
- Average days between sessions
- Longest gap (flag if >3 days)
- Late-night sessions (after midnight) — recovery risk for 44M
- Back-to-back days with shared muscle group — name the specific overlap

### 6. RECOMP PROGRESS ANALYSIS
- At 0.5kg/week pace: expected 2.0kg lost in 30 days
- Calorie targets: TDEE ~= 87 x 32 = 2,784 kcal → deficit target 2,367 kcal/day (-417 kcal)
- Protein target: 174g/day (2g/kg)
- Volume adequacy for muscle retention under deficit
- Deload status: weeks since last deload, next deload due in week X

### 7. RESEARCH INSIGHTS
For Ganesh's profile (44M, recomp, posterior chain focus):
- Age-specific recovery: 48-72h needed between same-muscle sessions
- Best lifts for his strength-to-injury-risk profile
- Rear delt / trap priority: posture and shoulder health context
- MEV vs MRV zone for each muscle group based on current sets/week
- Technique or programming red flags from session data
- If prior report exists: is the overall trajectory positive?

### 8. NEXT WEEK PLAN
- Sessions to prioritize (which days, which muscle groups)
- Exercises to add or increase
- Specific weight/rep adjustments based on progression logic
- Deload recommendation if applicable (flag if week 4 of mesocycle)

---

## Append command

Run this to append (replace REPORT_FILE with the actual filename):

```bash
python3 - <<'PYEOF'
import glob, datetime

today = datetime.date.today().isoformat()
files = [f for f in glob.glob("report_*.txt") if today in f]
if not files:
    print("ERROR: no report file for today"); exit(1)

path = files[0]

sections = """
5. RECOVERY & CONSISTENCY
[write content here]

6. RECOMP PROGRESS ANALYSIS
[write content here]

7. RESEARCH INSIGHTS
[write content here]

8. NEXT WEEK PLAN
[write content here]
"""
# DO NOT run this template literally — write the actual content above
PYEOF
```

**Do not run the template above.** Instead, write the actual section content directly by appending to the report file using the Bash tool with a heredoc, or the Write tool in append mode.
