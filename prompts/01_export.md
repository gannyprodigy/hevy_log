# TASK 1 OF 7: Export workout data

## STRICT RULES FOR THIS TASK
- Do THIS TASK ONLY. Do not read any other prompt files.
- Do not write any reports, summaries, or analysis.
- Do not look ahead at what other tasks exist.
- When done, output your summary and STOP. The next task will be sent to you automatically.

---

## Your only job right now

Run the Hevy workout export:

```bash
HEVY_API_KEY=$HEVY_API_KEY python3 hevy_trainer.py export
```

If it prints `[ERROR]`, stop and report the error.

## After the export completes

1. Find the generated `*_hevylog.txt` file
2. Read it
3. Output a brief summary:
   - Filename
   - Date range
   - Number of sessions
   - Total volume (kg x reps)
   - Session list with IST start times
   - Any anomalies (0 sessions, errors)

Then STOP. Do not do anything else.
