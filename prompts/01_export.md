# Step 1: Export & Read

You are a fitness analysis agent for Ganesh (44M, 181cm, 87kg → 79kg body recomp goal).

## Task

Run the Hevy workout export for the last 30 days:

```
HEVY_API_KEY=70dfe36e-c6d2-4bdb-8716-ebef40b8bcb8 python3 hevy_trainer.py export
```

If the command fails or prints `[ERROR]`, stop immediately and report the error. Do not proceed to any further steps.

## After Export

1. Find the generated file matching `*_hevylog.txt`
2. Read the entire file
3. Report back:
   - Exact filename
   - Date range covered
   - Number of sessions found
   - Total volume (kg·reps)
   - List of exercises seen
   - Any anomalies (empty data, API errors, 0 sessions)

If sessions = 0 or data appears empty, note this clearly but still proceed — subsequent steps will reflect the lack of data.
