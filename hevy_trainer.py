#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         HEVY TRAINER — UNIFIED INTELLIGENCE SYSTEM          ║
║  Ganesh | 44M | 181cm | 87kg → 79kg (Body Recomp)           ║
╠══════════════════════════════════════════════════════════════╣
║  1. Auto-Progression   – status of every tracked exercise    ║
║  2. Weekly Report      – day-by-day + per-exercise volume    ║
║  3. Muscle Balance     – push/pull, rear delt & trap depth   ║
║  4. Deload Automator   – schedule + progression history      ║
║  5. PR Tracker         – all lifts ranked + trend signals    ║
║  6. Recomp Monitor     – 4-week trends + fat loss math       ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  python3 hevy_trainer.py              # all features
  python3 hevy_trainer.py progression  # feature 1 only
  python3 hevy_trainer.py report       # feature 2 only
  python3 hevy_trainer.py balance      # feature 3 only
  python3 hevy_trainer.py deload       # feature 4 only
  python3 hevy_trainer.py prs          # feature 5 only
  python3 hevy_trainer.py recomp       # feature 6 only
  python3 hevy_trainer.py export       # export this week's data to plain-text log
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# ─── Configuration ────────────────────────────────────────────────────────────

API_KEY    = os.environ.get("HEVY_API_KEY", "")
BASE_URL   = "https://api.hevyapp.com/v1"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hevy_state.json")

TRAINER_FOLDER_NAME  = None   # None = track all routines
DELOAD_EVERY_N_WEEKS = 4

REAR_DELT_MIN_SETS_WEEK = 8
TRAP_MIN_SETS_WEEK      = 6

USER = {
    "name":      "Ganesh",
    "age":       44,
    "weight_kg": 87,
    "target_kg": 79,
    "height_cm": 181,
}

INCREMENT = {"compound": 2.5, "isolation": 1.25}

COMPOUND_KEYWORDS = [
    "bench press", "squat", "deadlift", "row", "pull up",
    "lat pulldown", "shoulder press", "overhead press",
    "hip thrust", "leg press",
]

MUSCLE_MAP = {
    "chest":      ["bench press", "chest fly", "chest press", "incline", "decline", "dip"],
    "back":       ["row", "pull up", "lat pulldown", "deadlift", "pulldown"],
    "shoulders":  ["shoulder press", "lateral raise", "overhead press"],
    "traps":      ["shrug", "deadlift", "trap"],
    "rear_delts": ["face pull", "rear delt", "reverse fly"],
    "biceps":     ["curl", "hammer curl", "bicep"],
    "triceps":    ["tricep", "pushdown", "dip"],
    "legs":       [
        "squat", "leg press", "leg extension", "leg curl", "lunge",
        "hack squat", "hip thrust", "hip abduction", "hip adduction",
        "romanian deadlift", "walking lunge",
    ],
    "core":       ["crunch", "plank", "leg raise", "ab"],
}

# ─── State ────────────────────────────────────────────────────────────────────

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "last_report_date":   None,
        "week_count":         0,
        "last_deload_week":   0,
        "last_counted_week":  None,
        "progression_log":    [],
        "prs":                {},
        "weekly_snapshots":   [],   # [{week, vol_by_muscle, sessions, total_vol}]
        "strength_history":   {},   # {exercise: [{date, e1rm}]}
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)

# ─── API Helpers ──────────────────────────────────────────────────────────────

def api_request(method, path, data=None, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body    = json.dumps(data).encode() if data else None
    headers = {"api-key": API_KEY}
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {method} {path}: {e.read().decode()[:200]}")
        return {}

def api_get(path, params=None):
    return api_request("GET", path, params=params)

def api_put(path, data):
    return api_request("PUT", path, data=data)

def get_all_pages(path, key, page_size=10):
    results, page = [], 1
    while True:
        data  = api_get(path, {"page": page, "pageSize": page_size})
        items = data.get(key, [])
        results.extend(items)
        if len(items) < page_size:
            break
        page += 1
    return results

# ─── Data Fetchers ────────────────────────────────────────────────────────────

def get_trainer_routines():
    all_routines = get_all_pages("/routines", "routines")
    if not TRAINER_FOLDER_NAME:
        return all_routines
    folders = get_all_pages("/routine_folders", "routine_folders")
    folder  = next((f for f in folders if TRAINER_FOLDER_NAME in f.get("title", "")), None)
    if not folder:
        print(f"  [!] Folder '{TRAINER_FOLDER_NAME}' not found — using all routines.")
        return all_routines
    return [r for r in all_routines if r.get("folder_id") == folder["id"]]

def get_recent_workouts(days=7):
    cutoff   = datetime.now(timezone.utc) - timedelta(days=days)
    workouts = []
    page     = 1
    while True:
        data  = api_get("/workouts", {"page": page, "pageSize": 10})
        batch = data.get("workouts", [])
        if not batch:
            break
        for w in batch:
            ts = w.get("created_at") or w.get("start_time", "")
            try:
                created = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue
            if created >= cutoff:
                workouts.append(w)
        oldest = batch[-1].get("created_at") or batch[-1].get("start_time", "")
        try:
            oldest_dt = datetime.fromisoformat(oldest.replace("Z", "+00:00"))
        except Exception:
            break
        if oldest_dt < cutoff or len(batch) < 10:
            break
        page += 1
    return workouts

def get_exercise_history(template_id, count=5):
    data = api_get(f"/exercise_history/{template_id}", {"page": 1, "pageSize": count})
    return data.get("exercise_history", [])

def get_workout_count():
    data = api_get("/workouts/count")
    return data.get("workout_count", 0)

# ─── Utilities ────────────────────────────────────────────────────────────────

def classify_muscles(title):
    t = title.lower()
    return [m for m, kws in MUSCLE_MAP.items() if any(k in t for k in kws)] or ["other"]

def is_compound(title):
    return any(k in title.lower() for k in COMPOUND_KEYWORDS)

def e1rm(weight, reps):
    return weight if reps == 1 else round(weight * (1 + reps / 30), 1)

def parse_ts(w):
    ts = w.get("created_at") or w.get("start_time", "")
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

def bar(value, max_value, width=20, fill="█", empty="░"):
    filled = int(round(value / max_value * width)) if max_value > 0 else 0
    return fill * filled + empty * (width - filled)

def section(title):
    print(f"\n{'='*64}")
    print(f"  {title}")
    print(f"{'='*64}")

# ─── Feature 1: Auto-Progression ──────────────────────────────────────────────

def run_auto_progression(state):
    section("1  AUTO-PROGRESSION")

    routines = get_trainer_routines()
    if not routines:
        print("  No routines found.")
        return state

    total_updates  = []
    all_statuses   = []   # for summary table

    for routine in routines:
        updated_exercises = []
        routine_changed   = False

        print(f"\n  Routine: {routine['title']}")
        print(f"  {'─'*58}")

        for ex in routine.get("exercises", []):
            template_id = ex.get("exercise_template_id")
            title       = ex.get("title", "Unknown")
            all_sets    = ex.get("sets", [])
            working     = [s for s in all_sets if s.get("type") == "normal"]

            if not working or not template_id:
                updated_exercises.append(ex)
                continue

            rep_ceil = working[0].get("rep_range_end") or working[0].get("reps")
            rep_floor = working[0].get("rep_range_start") or rep_ceil
            cur_wt   = working[0].get("weight_kg") or 0
            n_sets   = len(working)

            if not rep_ceil or cur_wt == 0:
                updated_exercises.append(ex)
                print(f"    {title:42s}  [no target reps set]")
                continue

            history = get_exercise_history(template_id, count=5)
            if not history:
                updated_exercises.append(ex)
                print(f"    {title:42s}  [no history yet]")
                continue

            last_entry  = history[0]
            last_date   = (last_entry.get("date") or "")[:10]
            last_w_sets = [s for s in last_entry.get("sets", []) if s.get("indicator") != "warmup"]

            if not last_w_sets:
                updated_exercises.append(ex)
                print(f"    {title:42s}  [no working sets logged]")
                continue

            sets_hit    = sum(1 for s in last_w_sets if s.get("reps", 0) >= rep_ceil)
            sets_total  = len(last_w_sets)
            last_reps   = [s.get("reps", 0) for s in last_w_sets]
            last_wts    = [s.get("weight_kg", 0) for s in last_w_sets]
            best_e1rm   = max(e1rm(w, r) for w, r in zip(last_wts, last_reps) if w and r)

            range_str   = f"{rep_floor}–{rep_ceil}" if rep_floor != rep_ceil else str(rep_ceil)

            if sets_hit == sets_total:
                # Trigger progression
                inc    = INCREMENT["compound"] if is_compound(title) else INCREMENT["isolation"]
                new_wt = round(cur_wt + inc, 2)
                status = f"PROGRESSED  {cur_wt}kg → {new_wt}kg  (+{inc}kg)"

                new_sets = []
                for s in all_sets:
                    sc = dict(s)
                    if sc.get("type") == "normal":
                        sc["weight_kg"] = new_wt
                    new_sets.append(sc)
                ex_copy         = dict(ex)
                ex_copy["sets"] = new_sets
                updated_exercises.append(ex_copy)
                routine_changed = True
                total_updates.append({
                    "routine": routine["title"], "exercise": title,
                    "old_weight": cur_wt, "new_weight": new_wt, "increment": inc,
                    "date": datetime.now().isoformat()
                })
            elif sets_hit >= sets_total - 1 and sets_total > 1:
                status = f"NEAR        {cur_wt}kg  ({sets_hit}/{sets_total} sets hit {rep_ceil} reps)  last: {last_date}"
                updated_exercises.append(ex)
            else:
                reps_str = "/".join(str(r) for r in last_reps)
                status   = f"WAITING     {cur_wt}kg  target {range_str} reps  last: {reps_str}  ({last_date})"
                updated_exercises.append(ex)

            cmp_tag = "[C]" if is_compound(title) else "[I]"
            print(f"    {cmp_tag} {title:39s}  {n_sets}×sets  e1RM: {best_e1rm:5.1f}kg  {status}")
            all_statuses.append((title, status))

        if routine_changed:
            payload = {
                "routine": {
                    "title":     routine["title"],
                    "folder_id": routine.get("folder_id"),
                    "notes":     routine.get("notes", ""),
                    "exercises": updated_exercises,
                }
            }
            result = api_put(f"/routines/{routine['id']}", payload)
            if not result:
                print(f"\n  [!] Failed to save routine: {routine['title']}")

    # Summary
    progressed = [s for _, s in all_statuses if s.startswith("PROGRESSED")]
    near       = [s for _, s in all_statuses if s.startswith("NEAR")]
    print(f"\n  Summary: {len(progressed)} progressed, {len(near)} near, "
          f"{len(all_statuses)-len(progressed)-len(near)} waiting")

    if total_updates:
        state.setdefault("progression_log", []).append({
            "date":    datetime.now().isoformat(),
            "updates": total_updates,
        })
        state["progression_log"] = state["progression_log"][-50:]

    return state

# ─── Feature 2: Weekly Report ─────────────────────────────────────────────────

def run_weekly_report(state):
    section(f"2  WEEKLY REPORT  —  w/e {datetime.now().strftime('%d %b %Y')}")

    workouts = get_recent_workouts(days=7)
    print(f"\n  Sessions this week: {len(workouts)} / 5 planned")

    # Day-by-day breakdown
    if workouts:
        print(f"\n  Day-by-Day:")
        for w in sorted(workouts, key=lambda x: parse_ts(x) or datetime.min):
            dt       = parse_ts(w)
            day_str  = dt.strftime("%a %d %b  %H:%M") if dt else "Unknown"
            n_ex     = len(w.get("exercises", []))
            n_sets   = sum(
                len([s for s in ex.get("sets", []) if s.get("type") == "normal"])
                for ex in w.get("exercises", [])
            )
            w_vol    = sum(
                (s.get("weight_kg") or 0) * (s.get("reps") or 0)
                for ex in w.get("exercises", [])
                for s in ex.get("sets", [])
                if s.get("type") == "normal"
            )
            title    = w.get("title") or w.get("name") or "Workout"
            print(f"    {day_str}  {title:28s}  {n_ex} exercises  {n_sets} sets  {w_vol:,.0f} kg·reps")

    # Per-exercise breakdown
    ex_vol   = defaultdict(float)
    ex_sets  = defaultdict(int)
    ex_best  = {}

    for w in workouts:
        for ex in w.get("exercises", []):
            title   = ex.get("title", "")
            w_sets  = [s for s in ex.get("sets", []) if s.get("type") == "normal"]
            for s in w_sets:
                wt   = s.get("weight_kg") or 0
                reps = s.get("reps") or 0
                ex_vol[title]  += wt * reps
                ex_sets[title] += 1
                if wt and reps:
                    est = e1rm(wt, reps)
                    if title not in ex_best or est > ex_best[title]:
                        ex_best[title] = est

    if ex_vol:
        print(f"\n  Exercise Breakdown  (sets | volume | best e1RM):")
        for title in sorted(ex_vol, key=lambda t: ex_vol[t], reverse=True):
            e1rm_str = f"{ex_best[title]:.1f}kg e1RM" if title in ex_best else "—"
            print(f"    {title:42s}  {ex_sets[title]:2d} sets  {ex_vol[title]:>8,.0f} kg·reps  {e1rm_str}")

    # Volume by muscle group
    vol_by_muscle  = defaultdict(float)
    sets_by_muscle = defaultdict(int)
    for w in workouts:
        for ex in w.get("exercises", []):
            muscles = classify_muscles(ex.get("title", ""))
            for s in ex.get("sets", []):
                if s.get("type") == "normal":
                    vol = (s.get("weight_kg") or 0) * (s.get("reps") or 0)
                    for m in muscles:
                        vol_by_muscle[m]  += vol
                        sets_by_muscle[m] += 1

    total_vol = sum(vol_by_muscle.values())
    print(f"\n  Volume by Muscle Group  (total: {total_vol:,.0f} kg·reps):")
    order = ["rear_delts", "traps", "back", "chest", "shoulders", "legs", "biceps", "triceps", "core"]
    max_vol = max(vol_by_muscle.values()) if vol_by_muscle else 1
    for m in order:
        if m in vol_by_muscle:
            pct   = vol_by_muscle[m] / total_vol * 100
            b     = bar(vol_by_muscle[m], max_vol, width=16)
            flag  = "  ★ PRIORITY" if m in ("rear_delts", "traps") else ""
            warn  = ""
            if m == "rear_delts" and sets_by_muscle[m] < REAR_DELT_MIN_SETS_WEEK:
                warn = f"  ⚠ only {sets_by_muscle[m]} sets (target {REAR_DELT_MIN_SETS_WEEK}+)"
            if m == "traps" and sets_by_muscle[m] < TRAP_MIN_SETS_WEEK:
                warn = f"  ⚠ only {sets_by_muscle[m]} sets (target {TRAP_MIN_SETS_WEEK}+)"
            label = m.replace("_", " ").title()
            print(f"    {label:15s}  {b}  {vol_by_muscle[m]:>8,.0f}  {pct:4.1f}%  ({sets_by_muscle[m]} sets){flag}{warn}")

    # Save weekly snapshot to state
    iso_week = list(datetime.now().isocalendar()[:2])
    snap = {
        "week":         iso_week,
        "date":         datetime.now().strftime("%Y-%m-%d"),
        "sessions":     len(workouts),
        "total_vol":    round(total_vol, 1),
        "vol_by_muscle": {k: round(v, 1) for k, v in vol_by_muscle.items()},
        "sets_by_muscle": dict(sets_by_muscle),
    }
    snaps = state.get("weekly_snapshots", [])
    # Replace if same week already recorded
    snaps = [s for s in snaps if s.get("week") != iso_week]
    snaps.append(snap)
    state["weekly_snapshots"] = snaps[-16:]   # keep 16 weeks
    state["last_report_date"] = datetime.now().isoformat()
    return state

# ─── Feature 3: Muscle Balance ────────────────────────────────────────────────

def run_muscle_balance(state):
    section("3  MUSCLE BALANCE  —  4-week rolling window")

    workouts = get_recent_workouts(days=28)

    push_ex  = defaultdict(float)
    pull_ex  = defaultdict(float)
    vol_by_m = defaultdict(float)
    sets_by_m = defaultdict(int)

    for w in workouts:
        for ex in w.get("exercises", []):
            t      = ex.get("title", "")
            tl     = t.lower()
            w_sets = [s for s in ex.get("sets", []) if s.get("type") == "normal"]
            vol    = sum((s.get("weight_kg") or 0) * (s.get("reps") or 0) for s in w_sets)
            n_sets = len(w_sets)

            if any(k in tl for k in ["bench", "chest", "shoulder press", "lateral raise",
                                      "tricep", "dip", "incline", "decline", "overhead"]):
                push_ex[t] += vol
            if any(k in tl for k in ["row", "pull up", "lat pulldown", "curl", "deadlift",
                                      "face pull", "rear delt", "reverse fly", "shrug"]):
                pull_ex[t] += vol

            for m in classify_muscles(t):
                vol_by_m[m]  += vol
                sets_by_m[m] += n_sets

    push_vol = sum(push_ex.values())
    pull_vol = sum(pull_ex.values())
    ratio    = (pull_vol / push_vol) if push_vol > 0 else 0

    print(f"\n  Push:Pull Ratio  (target ≥ 1.0)")
    print(f"    Push volume : {push_vol:>10,.0f} kg·reps")
    print(f"    Pull volume : {pull_vol:>10,.0f} kg·reps")
    status = "OK" if ratio >= 1.0 else "LOW — increase rowing/pulling work"
    print(f"    Ratio       : {ratio:.2f}   {status}")

    print(f"\n  Push breakdown:")
    for ex, vol in sorted(push_ex.items(), key=lambda x: x[1], reverse=True):
        print(f"    {ex:42s}  {vol:>8,.0f} kg·reps")

    print(f"\n  Pull breakdown:")
    for ex, vol in sorted(pull_ex.items(), key=lambda x: x[1], reverse=True):
        print(f"    {ex:42s}  {vol:>8,.0f} kg·reps")

    # Priority muscles
    rear_sets = sets_by_m.get("rear_delts", 0)
    trap_sets = sets_by_m.get("traps", 0)
    target_rd = REAR_DELT_MIN_SETS_WEEK * 4
    target_tr = TRAP_MIN_SETS_WEEK * 4

    print(f"\n  Priority Muscle Depth  (4 weeks):")
    rd_bar = bar(rear_sets, target_rd, width=20)
    tr_bar = bar(trap_sets, target_tr, width=20)
    print(f"    Rear Delts  {rd_bar}  {rear_sets:>3} sets  (target {target_rd}+)  "
          f"{'OK' if rear_sets >= target_rd else 'LOW'}")
    print(f"    Traps       {tr_bar}  {trap_sets:>3} sets  (target {target_tr}+)  "
          f"{'OK' if trap_sets >= target_tr else 'LOW'}")

    # Weekly snapshots trend (from state)
    snaps = state.get("weekly_snapshots", [])[-4:]
    if len(snaps) >= 2:
        print(f"\n  4-Week Volume Trend by Muscle:")
        all_muscles = sorted({m for s in snaps for m in s.get("vol_by_muscle", {})})
        header = f"    {'Muscle':15s}" + "".join(f"  {s['date'][5:]:>7}" for s in snaps)
        print(header)
        print(f"    {'─'*55}")
        for m in all_muscles:
            vals = [s.get("vol_by_muscle", {}).get(m, 0) for s in snaps]
            row  = f"    {m.replace('_',' ').title():15s}"
            for v in vals:
                row += f"  {v:>7,.0f}"
            # Trend arrow
            if len(vals) >= 2 and vals[-2] > 0:
                chg = (vals[-1] - vals[-2]) / vals[-2] * 100
                row += f"  {'↑' if chg > 5 else ('↓' if chg < -5 else '→')} {chg:+.0f}%"
            print(row)

    return state

# ─── Feature 4: Deload Automator ──────────────────────────────────────────────

def run_deload_check(state):
    section("4  DELOAD AUTOMATOR")

    current_iso_week = datetime.now().isocalendar()[:2]
    if state.get("last_counted_week") != list(current_iso_week):
        state["week_count"]        = state.get("week_count", 0) + 1
        state["last_counted_week"] = list(current_iso_week)

    since_deload = state["week_count"] - state.get("last_deload_week", 0)
    weeks_left   = DELOAD_EVERY_N_WEEKS - since_deload
    total_wkts   = get_workout_count()

    print(f"\n  Total workouts logged : {total_wkts}")
    print(f"  Training weeks        : {state['week_count']}")
    print(f"  Weeks since deload    : {since_deload} / {DELOAD_EVERY_N_WEEKS}")
    print(f"  Deload progress       : {bar(since_deload, DELOAD_EVERY_N_WEEKS, width=20)}")

    if since_deload >= DELOAD_EVERY_N_WEEKS:
        print(f"\n  ⚠ DELOAD WEEK — cutting to 2 working sets, same weight.")
        routines = get_trainer_routines()
        for routine in routines:
            new_exs = []
            for ex in routine.get("exercises", []):
                ec      = dict(ex)
                warmups = [s for s in ec.get("sets", []) if s.get("type") == "warmup"]
                work    = [s for s in ec.get("sets", []) if s.get("type") == "normal"][:2]
                ec["sets"]  = warmups + work
                ec["notes"] = ((ec.get("notes") or "") + " [DELOAD: 2 sets, same weight]").strip()
                new_exs.append(ec)
            payload = {
                "routine": {
                    "title":     routine["title"],
                    "folder_id": routine.get("folder_id"),
                    "notes":     "DELOAD WEEK — 2 sets per exercise, same weight. Focus on form & recovery.",
                    "exercises": new_exs,
                }
            }
            api_put(f"/routines/{routine['id']}", payload)
            print(f"  Updated: {routine['title']}")
        state["last_deload_week"] = state["week_count"]
    else:
        print(f"\n  Next deload in {weeks_left} week(s). Keep pushing.")

    # Progression history
    log = state.get("progression_log", [])
    if log:
        print(f"\n  Recent Progression History  (last {min(len(log), 10)} runs):")
        for entry in log[-10:]:
            date_str = entry.get("date", "")[:10]
            for u in entry.get("updates", []):
                print(f"    {date_str}  {u['exercise']:42s}  "
                      f"{u['old_weight']}kg → {u['new_weight']}kg  (+{u['increment']}kg)")
    else:
        print("\n  No progressions recorded yet.")

    return state

# ─── Feature 5: PR Tracker ────────────────────────────────────────────────────

def run_pr_tracker(state):
    section("5  PERSONAL RECORDS")

    workouts_7d  = get_recent_workouts(days=7)
    workouts_30d = get_recent_workouts(days=30)
    workouts_90d = get_recent_workouts(days=90)
    stored_prs   = state.get("prs", {})
    strength_h   = state.get("strength_history", {})
    new_prs      = []

    # Update PRs and strength history from last 7 days
    for w in workouts_7d:
        dt = parse_ts(w)
        for ex in w.get("exercises", []):
            title  = ex.get("title", "")
            w_sets = [s for s in ex.get("sets", []) if s.get("type") == "normal"]
            for s in w_sets:
                wt   = s.get("weight_kg") or 0
                reps = s.get("reps") or 0
                if not wt or not reps:
                    continue
                est  = e1rm(wt, reps)
                prev = stored_prs.get(title, {}).get("e1rm", 0)
                if est > prev:
                    if prev > 0:
                        new_prs.append((title, prev, est, wt, reps))
                    stored_prs[title] = {
                        "e1rm":   est,
                        "weight": wt,
                        "reps":   reps,
                        "date":   (w.get("created_at") or "")[:10],
                    }
                # Track strength history
                if dt:
                    strength_h.setdefault(title, [])
                    entry = {"date": dt.strftime("%Y-%m-%d"), "e1rm": est, "weight": wt, "reps": reps}
                    if not any(e["date"] == entry["date"] and e["e1rm"] == est for e in strength_h[title]):
                        strength_h[title].append(entry)
                        strength_h[title] = sorted(strength_h[title], key=lambda x: x["date"])[-20:]

    if new_prs:
        print(f"\n  NEW PRs THIS WEEK:")
        for title, old, new, wt, reps in new_prs:
            print(f"    + {title:42s}  {old:.1f} → {new:.1f} kg e1RM  ({wt}kg × {reps})")
    else:
        print(f"\n  No new PRs this week.")

    # All lifts ranked
    print(f"\n  All Lifts Ranked by e1RM:")
    print(f"    {'Exercise':42s}  {'e1RM':>6}  {'Set':>12}  {'Date':>10}  Trend")
    print(f"    {'─'*80}")
    for name, pr in sorted(stored_prs.items(), key=lambda x: x[1]["e1rm"], reverse=True):
        # Trend: compare best in last 30d vs 30–90d
        def best_e1rm_in(workouts):
            best = 0
            for w in workouts:
                for ex in w.get("exercises", []):
                    if ex.get("title") != name:
                        continue
                    for s in ex.get("sets", []):
                        if s.get("type") == "normal":
                            wt2 = s.get("weight_kg") or 0
                            r2  = s.get("reps") or 0
                            if wt2 and r2:
                                best = max(best, e1rm(wt2, r2))
            return best

        recent_best  = best_e1rm_in(workouts_30d)
        older_ids    = {w["id"] for w in workouts_30d}
        older_wkts   = [w for w in workouts_90d if w["id"] not in older_ids]
        older_best   = best_e1rm_in(older_wkts)

        if older_best == 0:
            trend = "new"
        elif recent_best > older_best * 1.02:
            trend = f"↑ +{recent_best - older_best:.1f}kg"
        elif recent_best < older_best * 0.98:
            trend = f"↓ -{older_best - recent_best:.1f}kg"
        else:
            trend = "→ stable"

        set_str = f"{pr['weight']}kg×{pr['reps']}"
        print(f"    {name:42s}  {pr['e1rm']:>6.1f}  {set_str:>12}  {pr['date']:>10}  {trend}")

    state["prs"]              = stored_prs
    state["strength_history"] = strength_h
    return state

# ─── Feature 6: Recomp Monitor ────────────────────────────────────────────────

def run_recomp_monitor(state):
    section(f"6  BODY RECOMP MONITOR  —  {USER['name']} {USER['weight_kg']}kg → {USER['target_kg']}kg")

    # Fetch all windows
    wk2_4 = get_recent_workouts(days=28)

    # Split into 4 individual weeks
    weeks = []
    for i in range(4):
        lo = timedelta(days=i * 7)
        hi = timedelta(days=(i + 1) * 7)
        wkts = [
            w for w in wk2_4
            if parse_ts(w) and
            (datetime.now(timezone.utc) - hi) <= parse_ts(w) < (datetime.now(timezone.utc) - lo)
        ]
        weeks.insert(0, wkts)   # index 3 = most recent

    def total_vol(wkts):
        return sum(
            (s.get("weight_kg") or 0) * (s.get("reps") or 0)
            for w in wkts
            for ex in w.get("exercises", [])
            for s in ex.get("sets", [])
            if s.get("type") == "normal"
        )

    vols     = [total_vol(w) for w in weeks]
    sessions = [len(w) for w in weeks]
    avg_sess = sum(sessions) / 4

    # Week-by-week table
    print(f"\n  4-Week Training Summary:")
    print(f"    {'Week':>6}  {'Sessions':>8}  {'Volume (kg·reps)':>18}  Bar")
    print(f"    {'─'*55}")
    max_vol = max(vols) if any(v > 0 for v in vols) else 1
    labels  = ["wk -3", "wk -2", "wk -1", "this wk"]
    for i, (label, sess, vol) in enumerate(zip(labels, sessions, vols)):
        b = bar(vol, max_vol, width=16)
        print(f"    {label:>6}  {sess:>8}  {vol:>18,.0f}  {b}")

    # Volume trend
    this_vol = vols[3]
    last_vol = vols[2]
    change   = ((this_vol - last_vol) / last_vol * 100) if last_vol > 0 else 0
    print(f"\n  Volume change (this vs last week): {change:+.1f}%  ", end="")
    if change < -20:
        print("SIGNIFICANT DROP — muscle loss risk")
    elif change < -10:
        print("Slight drop — watch next week")
    elif change > 20:
        print("Spike — ensure 48-72h recovery (age 44)")
    else:
        print("Stable — ideal for recomposition")

    print(f"  4-week avg: {avg_sess:.1f} sessions/week  ", end="")
    print("Consistent" if avg_sess >= 4 else "⚠ Below target — aim for 5/week")

    # Recovery gap analysis
    all_dates = sorted(
        [parse_ts(w) for w in wk2_4 if parse_ts(w)],
        reverse=True
    )
    if len(all_dates) >= 2:
        gaps = [(all_dates[i] - all_dates[i+1]).days for i in range(len(all_dates)-1)]
        avg_gap = sum(gaps) / len(gaps)
        max_gap = max(gaps)
        print(f"\n  Recovery gaps (last 4 weeks):")
        print(f"    Avg days between sessions : {avg_gap:.1f}")
        print(f"    Longest gap               : {max_gap} days"
              f"  {'[OK]' if max_gap <= 3 else '[⚠ consider consistency]'}")

    # Recomp math
    kg_to_lose   = USER["weight_kg"] - USER["target_kg"]
    tdee         = int(USER["weight_kg"] * 32)
    target_cals  = int(tdee * 0.85)
    deficit_day  = tdee - target_cals
    weeks_to_goal = round(kg_to_lose / 0.5)

    bmi = USER["weight_kg"] / (USER["height_cm"] / 100) ** 2
    target_bmi = USER["target_kg"] / (USER["height_cm"] / 100) ** 2

    print(f"\n  Recomp Targets:")
    print(f"    Current weight  : {USER['weight_kg']} kg   BMI {bmi:.1f}")
    print(f"    Target weight   : {USER['target_kg']} kg   BMI {target_bmi:.1f}  (to lose {kg_to_lose} kg)")
    print(f"    At 0.5kg/week   : ~{weeks_to_goal} weeks to goal")
    print(f"\n  Nutrition (approx):")
    print(f"    Calories        : {target_cals} kcal/day  (15% deficit = -{deficit_day} kcal)")
    print(f"    Protein         : {int(USER['weight_kg'] * 2.0)}g/day  (2g/kg — muscle preservation)")
    print(f"    Carbs           : {int(target_cals * 0.40 / 4)}g/day  (40% carbs)")
    print(f"    Fat             : {int(target_cals * 0.25 / 9)}g/day  (25% fat)")

    # Consistency score
    possible   = 5 * 4   # 5 sessions/week × 4 weeks
    actual     = sum(sessions)
    score_pct  = actual / possible * 100
    score_bar  = bar(actual, possible, width=20)
    print(f"\n  Consistency Score (4 weeks):")
    print(f"    {score_bar}  {actual}/{possible} sessions  ({score_pct:.0f}%)")
    if score_pct >= 80:
        print(f"    Excellent — keep it up!")
    elif score_pct >= 60:
        print(f"    Good — aim to close the gap on missed sessions.")
    else:
        print(f"    Needs attention — consistency is your #1 lever for recomp.")

    return state

# ─── Export: Weekly Plain-Text Log ───────────────────────────────────────────

def get_week_workouts():
    """Return workouts that fall within the current ISO week (Mon–Sun, UTC)."""
    now = datetime.now(timezone.utc)
    # Monday 00:00 of the current ISO week
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7)

    workouts = []
    page = 1
    while True:
        data  = api_get("/workouts", {"page": page, "pageSize": 10})
        batch = data.get("workouts", [])
        if not batch:
            break
        for w in batch:
            ts = w.get("created_at") or w.get("start_time", "")
            try:
                created = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue
            if week_start <= created < week_end:
                workouts.append(w)
        # Stop if the oldest item in this page predates the week
        oldest_ts = batch[-1].get("created_at") or batch[-1].get("start_time", "")
        try:
            oldest_dt = datetime.fromisoformat(oldest_ts.replace("Z", "+00:00"))
        except Exception:
            break
        if oldest_dt < week_start or len(batch) < 10:
            break
        page += 1

    return workouts, week_start, week_end - timedelta(seconds=1)


def run_export_log(state):
    """Export this week's workout data to a plain-text file for AI analysis."""
    workouts, week_start, week_end = get_week_workouts()

    from_str = week_start.strftime("%Y-%m-%d")
    to_str   = week_end.strftime("%Y-%m-%d")
    filename = f"{from_str}_to_{to_str}_hevylog.txt"
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    lines = []
    def w(text=""):
        lines.append(text)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    w("=" * 72)
    w("HEVY WORKOUT LOG — WEEKLY EXPORT")
    w(f"Week   : {from_str} to {to_str}")
    w(f"Created: {now_str}")
    w(f"User   : {USER['name']} | {USER['age']}M | {USER['height_cm']}cm | "
      f"{USER['weight_kg']}kg → {USER['target_kg']}kg target")
    w("=" * 72)
    w()

    workouts_sorted = sorted(workouts, key=lambda x: parse_ts(x) or datetime.min)

    w(f"SESSIONS THIS WEEK: {len(workouts_sorted)} of 5 planned")
    w()

    # ── Per-session detail ──
    week_vol       = 0.0
    week_sets      = 0
    ex_agg         = defaultdict(lambda: {"sessions": 0, "sets": 0, "vol": 0.0, "best_e1rm": 0.0})
    vol_by_muscle  = defaultdict(float)
    sets_by_muscle = defaultdict(int)

    for idx, workout in enumerate(workouts_sorted, 1):
        dt      = parse_ts(workout)
        day_str = dt.strftime("%A %d %b %Y  %H:%M") if dt else "Unknown"
        title   = workout.get("title") or workout.get("name") or "Workout"

        # Duration
        start_ts = workout.get("start_time") or workout.get("created_at") or ""
        end_ts   = workout.get("end_time") or ""
        duration_str = ""
        if start_ts and end_ts:
            try:
                s = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                e = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
                mins = int((e - s).total_seconds() / 60)
                duration_str = f"  |  {mins} min"
            except Exception:
                pass

        w("-" * 72)
        w(f"SESSION {idx}: {day_str}{duration_str}")
        w(f"Title: {title}")
        if workout.get("notes"):
            w(f"Notes: {workout.get('notes')}")
        w()

        session_vol  = 0.0
        session_sets = 0

        for ex in workout.get("exercises", []):
            ex_title  = ex.get("title", "Unknown")
            muscles   = classify_muscles(ex_title)
            cmp_label = "compound" if is_compound(ex_title) else "isolation"
            all_sets  = ex.get("sets", [])

            w(f"  {ex_title}  [{cmp_label} | {', '.join(muscles)}]")
            if ex.get("notes"):
                w(f"    Notes: {ex.get('notes')}")

            ex_vol      = 0.0
            ex_sets_cnt = 0
            ex_best     = 0.0
            set_num     = 0

            for s in all_sets:
                wt       = s.get("weight_kg") or 0
                reps     = s.get("reps") or 0
                stype    = s.get("type", "normal")
                rpe      = s.get("rpe")
                rest     = s.get("rest_seconds")

                label = "Warmup" if stype == "warmup" else f"Set {set_num + 1}"
                if stype == "normal":
                    set_num += 1

                vol_set = wt * reps
                e1rm_val = e1rm(wt, reps) if wt and reps else 0.0

                parts = [f"{wt}kg × {reps} reps"]
                if vol_set:
                    parts.append(f"vol: {vol_set:,.0f} kg·reps")
                if e1rm_val and stype == "normal":
                    parts.append(f"e1RM: {e1rm_val:.1f}kg")
                if rpe:
                    parts.append(f"RPE: {rpe}")
                if rest:
                    parts.append(f"rest: {rest}s")

                w(f"    {label:<10}  {' | '.join(parts)}")

                if stype == "normal":
                    ex_vol      += vol_set
                    ex_sets_cnt += 1
                    if e1rm_val > ex_best:
                        ex_best = e1rm_val
                    for m in muscles:
                        vol_by_muscle[m]  += vol_set
                        sets_by_muscle[m] += 1

            # Per-exercise summary line
            best_str = f"  |  best e1RM: {ex_best:.1f}kg" if ex_best else ""
            w(f"    >> {ex_sets_cnt} working sets  |  volume: {ex_vol:,.0f} kg·reps{best_str}")
            w()

            session_vol  += ex_vol
            session_sets += ex_sets_cnt

            agg = ex_agg[ex_title]
            agg["sessions"] += 1
            agg["sets"]     += ex_sets_cnt
            agg["vol"]      += ex_vol
            if ex_best > agg["best_e1rm"]:
                agg["best_e1rm"] = ex_best

        week_vol  += session_vol
        week_sets += session_sets
        w(f"  SESSION TOTAL: {session_sets} sets  |  {session_vol:,.0f} kg·reps")
        w()

    # ── Weekly totals ──
    w("=" * 72)
    w("WEEKLY TOTALS")
    w("=" * 72)
    w(f"  Sessions  : {len(workouts_sorted)} of 5 planned")
    w(f"  Total sets: {week_sets}")
    w(f"  Total vol : {week_vol:,.0f} kg·reps")
    w()

    # ── Volume by muscle group ──
    w("VOLUME BY MUSCLE GROUP")
    w("-" * 72)
    total_vol = sum(vol_by_muscle.values()) or 1
    order = ["chest", "back", "shoulders", "traps", "rear_delts",
             "legs", "biceps", "triceps", "core", "other"]
    for m in order:
        if m in vol_by_muscle:
            pct   = vol_by_muscle[m] / total_vol * 100
            label = m.replace("_", " ").title()
            w(f"  {label:<15}  {vol_by_muscle[m]:>10,.0f} kg·reps  "
              f"{pct:5.1f}%  |  {sets_by_muscle[m]} sets")
    w()

    # ── Exercise summary ──
    w("EXERCISE SUMMARY  (sorted by volume)")
    w("-" * 72)
    for ex_title, agg in sorted(ex_agg.items(), key=lambda x: x[1]["vol"], reverse=True):
        muscles   = classify_muscles(ex_title)
        cmp_label = "C" if is_compound(ex_title) else "I"
        best_str  = f"  |  best e1RM: {agg['best_e1rm']:.1f}kg" if agg["best_e1rm"] else ""
        w(f"  [{cmp_label}] {ex_title:<44}  "
          f"{agg['sessions']} sess  {agg['sets']} sets  "
          f"{agg['vol']:>10,.0f} kg·reps{best_str}")
        w(f"      muscles: {', '.join(muscles)}")
    w()

    # ── Push / Pull balance ──
    w("PUSH / PULL BALANCE")
    w("-" * 72)
    push_vol = sum(
        agg["vol"] for t, agg in ex_agg.items()
        if any(k in t.lower() for k in ["bench", "chest", "shoulder press",
                                         "lateral raise", "tricep", "dip",
                                         "incline", "decline", "overhead"])
    )
    pull_vol = sum(
        agg["vol"] for t, agg in ex_agg.items()
        if any(k in t.lower() for k in ["row", "pull up", "lat pulldown",
                                          "curl", "deadlift", "face pull",
                                          "rear delt", "reverse fly", "shrug"])
    )
    ratio    = pull_vol / push_vol if push_vol else 0
    w(f"  Push volume : {push_vol:>10,.0f} kg·reps")
    w(f"  Pull volume : {pull_vol:>10,.0f} kg·reps")
    w(f"  Ratio       : {ratio:.2f}  ({'OK — balanced' if ratio >= 1.0 else 'LOW — increase pulling work'})")
    w()

    # ── Footer ──
    w("=" * 72)
    w(f"END OF LOG  |  {from_str} to {to_str}  |  Generated {now_str}")
    w("=" * 72)

    text = "\n".join(lines) + "\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    section(f"EXPORT — Weekly Log")
    print(f"\n  Week    : {from_str} to {to_str}")
    print(f"  Sessions: {len(workouts_sorted)}")
    print(f"  Volume  : {week_vol:,.0f} kg·reps  |  {week_sets} sets")
    print(f"\n  Saved → {filepath}")

    return state


# ─── Main ─────────────────────────────────────────────────────────────────────

MODES = {
    "progression": run_auto_progression,
    "report":      run_weekly_report,
    "balance":     run_muscle_balance,
    "deload":      run_deload_check,
    "prs":         run_pr_tracker,
    "recomp":      run_recomp_monitor,
    "export":      run_export_log,
}

def main():
    now = datetime.now()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          HEVY TRAINER — UNIFIED INTELLIGENCE SYSTEM         ║")
    print(f"║  {now.strftime('%A, %d %B %Y  %H:%M'):58s}║")
    print("╚══════════════════════════════════════════════════════════════╝")

    state = load_state()
    mode  = sys.argv[1] if len(sys.argv) > 1 else "all"

    try:
        if mode == "all":
            for fn in MODES.values():
                state = fn(state)
        elif mode in MODES:
            state = MODES[mode](state)
        else:
            print(f"Unknown mode '{mode}'. Options: {', '.join(MODES)} or 'all'")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise

    save_state(state)
    print(f"\n{'='*64}")
    print(f"  Done. State saved → {STATE_FILE}")

if __name__ == "__main__":
    main()
