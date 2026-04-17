# Step 3b: Report — Sections 3 and 4 (Strength + Muscle Balance)

Append sections 3 and 4 to the existing `report_YYYY-MM-DD.txt` (today's date).
Do NOT overwrite — append only.

```bash
ls -t report_*.txt | grep "$(date +%Y-%m-%d)" | head -1
```

Use plain ASCII only. Focus on this week. All times in IST.

---

## Append ONLY sections 3 and 4

### 3. STRENGTH: HOW ARE THE LIFTS MOVING?
For every exercise that appeared this week:
- Best weight x reps this week
- Best estimated 1-rep max (e1RM = weight x (1 + reps/30))
- Compared to the last time this exercise appeared in the 30-day log: up / same / down, and by how much
- What to do next session (specific weight and reps)
- Flag any: rep collapse between sets, weight drop mid-session, bodyweight exercise logged at 0kg

Group: main compound lifts first (rows, presses, deadlifts, squats), then isolation exercises.

### 4. ARE THE RIGHT MUSCLES GETTING ENOUGH WORK?
Plain text table for this week's sets per muscle group:

  Muscle Group    | Sets this wk | Target/wk | Gap    | Status
  ----------------+--------------+-----------+--------+--------
  ...

Explain in plain terms:
- Which muscles got enough work this week
- Which are short and why it matters in simple language
- Specifically flag: rear delts (need 8+ sets/week — shoulder health), traps (6+ sets/week)
- Push vs pull set count balance

---

Append using Bash heredoc or Python append mode.
