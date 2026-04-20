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
            ts = w.get("start_time") or w.get("created_at", "")
            try:
                created = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue
            if created >= cutoff:
                workouts.append(w)
        oldest = batch[-1].get("start_time") or batch[-1].get("created_at", "")
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
    ts = w.get("start_time") or w.get("created_at", "")
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

def get_week_workouts(days=30):
    """Return workouts from the last N days (default 30) for trend analysis."""
    now        = datetime.now(timezone.utc)
    from_date  = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    to_date    = now

    workouts = []
    page = 1
    while True:
        data  = api_get("/workouts", {"page": page, "pageSize": 10})
        batch = data.get("workouts", [])
        if not batch:
            break
        for w in batch:
            ts = w.get("start_time") or w.get("created_at", "")
            try:
                created = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue
            if from_date <= created <= to_date:
                workouts.append(w)
        oldest_ts = batch[-1].get("start_time") or batch[-1].get("created_at", "")
        try:
            oldest_dt = datetime.fromisoformat(oldest_ts.replace("Z", "+00:00"))
        except Exception:
            break
        if oldest_dt < from_date or len(batch) < 10:
            break
        page += 1

    return workouts, from_date, to_date


def run_export_log(state):
    """Export the last 30 days of workout data to a plain-text file for AI analysis."""
    workouts, from_date, to_date = get_week_workouts(days=30)

    from_str = from_date.strftime("%Y-%m-%d")
    to_str   = to_date.strftime("%Y-%m-%d")
    filename = f"{from_str}_to_{to_str}_hevylog.txt"
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    lines = []
    def w(text=""):
        lines.append(text)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    w("=" * 72)
    w("HEVY WORKOUT LOG — 30-DAY EXPORT")
    w(f"Period : {from_str} to {to_str}  (last 30 days)")
    w(f"Created: {now_str}")
    w(f"User   : {USER['name']} | {USER['age']}M | {USER['height_cm']}cm | "
      f"{USER['weight_kg']}kg → {USER['target_kg']}kg target")
    w("=" * 72)
    w()

    workouts_sorted = sorted(workouts, key=lambda x: parse_ts(x) or datetime.min)

    w(f"SESSIONS (last 30 days): {len(workouts_sorted)}  |  planned: ~{5*4} (5/wk × 4 wks)")
    w()

    # ── Per-session detail ──
    week_vol       = 0.0
    week_sets      = 0
    ex_agg         = defaultdict(lambda: {"sessions": 0, "sets": 0, "vol": 0.0, "best_e1rm": 0.0})
    vol_by_muscle  = defaultdict(float)
    sets_by_muscle = defaultdict(int)

    IST = timezone(timedelta(hours=5, minutes=30))
    for idx, workout in enumerate(workouts_sorted, 1):
        dt      = parse_ts(workout)
        dt_ist  = dt.astimezone(IST) if dt else None
        day_str = dt_ist.strftime("%A %d %b %Y  %H:%M IST") if dt_ist else "Unknown"
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
    w("30-DAY TOTALS")
    w("=" * 72)
    w(f"  Sessions  : {len(workouts_sorted)}  (planned ~20 for 30 days)")
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

    section(f"EXPORT — 30-Day Log")
    print(f"\n  Period  : {from_str} to {to_str}  (last 30 days)")
    print(f"  Sessions: {len(workouts_sorted)}")
    print(f"  Volume  : {week_vol:,.0f} kg·reps  |  {week_sets} sets")
    print(f"\n  Saved → {filepath}")

    return state


# ─── Analysis Report: Sections 1-6 (data-driven) ─────────────────────────────

def run_analysis_report(state):
    """Generate report sections 1-6 (data-driven) to report_YYYY-MM-DD.txt.

    Sections 7-8 (insights + next week plan) are appended by Claude.
    Uses plain ASCII only — no Unicode box-drawing characters.
    All times are displayed in IST (UTC+5:30).
    """
    IST = timezone(timedelta(hours=5, minutes=30))
    today_ist   = datetime.now(IST)
    report_date = today_ist.strftime("%Y-%m-%d")
    report_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"report_{report_date}.txt"
    )

    # ── Fetch 30-day data and split into this week vs prior ──
    workouts, _, _ = get_week_workouts(days=30)
    now_utc = datetime.now(timezone.utc)
    workouts_sorted = sorted(
        workouts,
        key=lambda x: parse_ts(x) or datetime.min.replace(tzinfo=timezone.utc)
    )

    week_cutoff_utc = (today_ist - timedelta(days=7)).astimezone(timezone.utc)
    this_week  = [w for w in workouts_sorted
                  if (parse_ts(w) or datetime.min.replace(tzinfo=timezone.utc)) >= week_cutoff_utc]
    prior_wks  = [w for w in workouts_sorted
                  if (parse_ts(w) or datetime.min.replace(tzinfo=timezone.utc)) < week_cutoff_utc]

    # ── Constants ──
    MUSCLE_TARGETS = {
        "chest":     12, "back":      14, "shoulders": 10,
        "traps":      6, "rear_delts": 8, "biceps":     8,
        "triceps":    8, "legs":      14, "core":        6,
    }
    MEV = {  # minimum effective volume to retain muscle on a calorie deficit
        "chest":  8, "back":      10, "shoulders": 8,
        "traps":  4, "rear_delts": 6, "biceps":    6,
        "triceps":6, "legs":      10, "core":       4,
    }
    TDEE        = 2784
    TARGET_CALS = 2367
    PROTEIN_G   = 174

    # ── Pre-compute: exercise sets for this week and prior ──
    ex_this_week = defaultdict(list)   # {title: [{"wt", "reps", "e1rm"}]}
    ex_prior     = defaultdict(list)   # {title: [{"wt", "reps", "e1rm", "date"}]}
    sets_by_muscle_week = defaultdict(int)
    vol_by_muscle_week  = defaultdict(float)

    for wk in this_week:
        for ex in wk.get("exercises", []):
            ex_title = ex.get("title", "Unknown")
            for s in ex.get("sets", []):
                if s.get("type", "normal") != "normal":
                    continue
                wt   = s.get("weight_kg") or 0
                reps = s.get("reps") or 0
                er   = e1rm(wt, reps) if wt and reps else 0.0
                ex_this_week[ex_title].append({"wt": wt, "reps": reps, "e1rm": er})
                for m in classify_muscles(ex_title):
                    sets_by_muscle_week[m] += 1
                    vol_by_muscle_week[m]  += wt * reps

    for wk in prior_wks:
        dt     = parse_ts(wk)
        dt_ist = dt.astimezone(IST) if dt else None
        dstr   = dt_ist.strftime("%d %b") if dt_ist else "?"
        for ex in wk.get("exercises", []):
            ex_title = ex.get("title", "Unknown")
            for s in ex.get("sets", []):
                if s.get("type", "normal") != "normal":
                    continue
                wt   = s.get("weight_kg") or 0
                reps = s.get("reps") or 0
                er   = e1rm(wt, reps) if wt and reps else 0.0
                if wt and reps:
                    ex_prior[ex_title].append({"wt": wt, "reps": reps, "e1rm": er, "date": dstr})

    # ── 4-week buckets (bucket 3 = this week, 0 = oldest) ──
    bucket_sessions = [0, 0, 0, 0]
    bucket_vol      = [0.0, 0.0, 0.0, 0.0]
    for wk in workouts_sorted:
        dt = parse_ts(wk)
        if not dt:
            continue
        days_ago = (now_utc - dt).total_seconds() / 86400
        if   days_ago <= 7:  b = 3
        elif days_ago <= 14: b = 2
        elif days_ago <= 21: b = 1
        elif days_ago <= 30: b = 0
        else:                continue
        bucket_sessions[b] += 1
        sv = 0.0
        for ex in wk.get("exercises", []):
            for s in ex.get("sets", []):
                if s.get("type", "normal") == "normal":
                    sv += (s.get("weight_kg") or 0) * (s.get("reps") or 0)
        bucket_vol[b] += sv

    def bucket_label(b):
        end_days   = (3 - b) * 7
        start_days = end_days + 7
        end_d   = (today_ist - timedelta(days=end_days)).strftime("%d %b")
        start_d = (today_ist - timedelta(days=start_days)).strftime("%d %b")
        return f"{start_d}-{end_d}"

    # ── Helpers ──
    lines = []
    def w(text=""):
        lines.append(str(text))

    def session_muscles(wk):
        ms = set()
        for ex in wk.get("exercises", []):
            for m in classify_muscles(ex.get("title", "")):
                ms.add(m)
        return ms

    def session_vol_sets(wk):
        vol, sets = 0.0, 0
        for ex in wk.get("exercises", []):
            for s in ex.get("sets", []):
                if s.get("type", "normal") == "normal":
                    vol  += (s.get("weight_kg") or 0) * (s.get("reps") or 0)
                    sets += 1
        return vol, sets

    # ────────────────────────────────────────────────────────────
    now_str   = today_ist.strftime("%Y-%m-%d %H:%M IST")
    wk_start  = (today_ist - timedelta(days=7)).strftime("%d %b")
    wk_end    = today_ist.strftime("%d %b %Y")
    sess_count = len(this_week)

    w("=" * 72)
    w("WEEKLY TRAINING REPORT")
    w(f"Generated : {now_str}")
    w(f"User      : {USER['name']} | {USER['age']}M | {USER['height_cm']}cm | "
      f"{USER['weight_kg']}kg -> {USER['target_kg']}kg")
    w(f"This week : {wk_start} to {wk_end}")
    w("=" * 72)
    w()

    # ════════════════════════════════════════════════════════════
    # SECTION 1: THIS WEEK AT A GLANCE
    # ════════════════════════════════════════════════════════════
    w("=" * 72)
    w("1. THIS WEEK AT A GLANCE")
    w("=" * 72)
    w()

    prior_counts = [bucket_sessions[b] for b in (0, 1, 2)]
    prior_avg    = sum(prior_counts) / 3 if prior_counts else 0

    w(f"  Sessions     : {sess_count} of 5 target")
    w(f"  Prior 3 weeks: {prior_counts[0]}, {prior_counts[1]}, {prior_counts[2]} sessions"
      f"  (avg {prior_avg:.1f})")
    w()

    # Score (1-10): sessions = 50%, muscle coverage = 30%, no red flags = 20%
    rd_sets = sets_by_muscle_week.get("rear_delts", 0)
    tr_sets = sets_by_muscle_week.get("traps", 0)
    late_count = sum(
        1 for wk in this_week
        if (lambda dt: dt is not None and 0 <= dt.astimezone(IST).hour < 4)(parse_ts(wk))
    )
    raw  = min(sess_count, 5) * 1.2
    raw += (1 if rd_sets >= 6 else 0) + (1 if tr_sets >= 4 else 0)
    raw -= late_count * 0.5
    score = max(1, min(10, round(raw)))
    if score >= 8:   score_note = "Strong week — volume, balance and recovery all solid."
    elif score >= 6: score_note = "Good week — one or two areas need attention (see below)."
    elif score >= 4: score_note = "Average week — muscle gaps or missed sessions holding you back."
    else:            score_note = "Below par — low sessions or major muscle imbalances this week."
    w(f"  Overall score: {score}/10 — {score_note}")
    w()

    # Biggest win
    best_ex, best_e1rm_v, best_set_data = None, 0.0, {}
    for ex_title, sets_list in ex_this_week.items():
        top_set = max(sets_list, key=lambda s: s["e1rm"], default=None)
        if top_set and top_set["e1rm"] > best_e1rm_v:
            best_e1rm_v = top_set["e1rm"]
            best_ex     = ex_title
            best_set_data = top_set

    if best_ex and best_e1rm_v > 0:
        w(f"  Biggest win  : {best_ex} — {best_set_data['wt']}kg x {best_set_data['reps']} reps"
          f"  (e1RM {best_e1rm_v:.1f}kg)")
    else:
        w("  Biggest win  : No working sets recorded this week")

    # Biggest concern: muscle furthest below target
    worst_muscle, worst_gap = None, 0
    for m, target in MUSCLE_TARGETS.items():
        gap = target - sets_by_muscle_week.get(m, 0)
        if gap > worst_gap:
            worst_gap, worst_muscle = gap, m
    if worst_muscle:
        actual = sets_by_muscle_week.get(worst_muscle, 0)
        w(f"  Biggest concern: {worst_muscle.replace('_',' ').title()} — "
          f"{actual} sets vs {MUSCLE_TARGETS[worst_muscle]} target ({worst_gap} sets short)")

    # Week-on-week volume
    this_vol = bucket_vol[3]
    last_vol = bucket_vol[2]
    if last_vol > 0:
        change_pct = (this_vol - last_vol) / last_vol * 100
        direction  = "UP" if change_pct >= 0 else "DOWN"
        w(f"  vs last week : Volume {direction} {abs(change_pct):.0f}%  "
          f"({this_vol:,.0f} vs {last_vol:,.0f} kg*reps)")
    else:
        w("  vs last week : No prior week data in 30-day log")
    w()

    # ════════════════════════════════════════════════════════════
    # SECTION 2: SESSION BY SESSION
    # ════════════════════════════════════════════════════════════
    w()
    w("=" * 72)
    w("2. THIS WEEK — SESSION BY SESSION")
    w("=" * 72)
    w()

    if not this_week:
        w("  No sessions recorded this week.")
    else:
        for idx, wk in enumerate(this_week, 1):
            dt     = parse_ts(wk)
            dt_ist = dt.astimezone(IST) if dt else None
            day_str = dt_ist.strftime("%A %d %b %Y  %H:%M IST") if dt_ist else "Unknown"
            title   = wk.get("title") or wk.get("name") or "Workout"

            # Duration
            s_ts = wk.get("start_time") or wk.get("created_at") or ""
            e_ts = wk.get("end_time") or ""
            dur_str = ""
            if s_ts and e_ts:
                try:
                    sd = datetime.fromisoformat(s_ts.replace("Z", "+00:00"))
                    ed = datetime.fromisoformat(e_ts.replace("Z", "+00:00"))
                    mins = int((ed - sd).total_seconds() / 60)
                    dur_str = f"  |  {mins} min"
                except Exception:
                    pass

            is_late  = dt_ist and 0 <= dt_ist.hour < 4
            late_tag = "  [FLAG: after midnight IST]" if is_late else ""

            sv, ss = session_vol_sets(wk)
            w(f"  Session {idx}: {day_str}{dur_str}{late_tag}")
            w(f"  Type   : {title}")
            w(f"  Volume : {sv:,.0f} kg*reps  |  {ss} sets")

            # Top exercises
            ex_lines = []
            for ex in wk.get("exercises", []):
                ex_title   = ex.get("title", "Unknown")
                norm_sets  = [s for s in ex.get("sets", []) if s.get("type", "normal") == "normal"]
                if not norm_sets:
                    continue
                best_s  = max(norm_sets, key=lambda s: e1rm(s.get("weight_kg") or 0, s.get("reps") or 0))
                bwt     = best_s.get("weight_kg") or 0
                breps   = best_s.get("reps") or 0
                ber     = e1rm(bwt, breps) if bwt and breps else 0
                ex_vol  = sum((s.get("weight_kg") or 0) * (s.get("reps") or 0) for s in norm_sets)

                # Flags
                flags_s = []
                reps_seq = [s.get("reps") or 0 for s in norm_sets]
                if len(reps_seq) >= 2 and reps_seq[0] > 0 and reps_seq[-1] < reps_seq[0] * 0.7:
                    flags_s.append(f"rep collapse {reps_seq[0]}->{reps_seq[-1]}")
                if bwt == 0 and breps > 0:
                    flags_s.append("0kg logged")
                wts_seq = [s.get("weight_kg") or 0 for s in norm_sets if (s.get("weight_kg") or 0) > 0]
                if len(wts_seq) >= 2 and wts_seq[-1] < wts_seq[0] * 0.9:
                    flags_s.append(f"weight drop {wts_seq[0]}kg->{wts_seq[-1]}kg")

                # Prior comparison
                prior_er = max((s["e1rm"] for s in ex_prior.get(ex_title, [])), default=0)
                if prior_er > 0 and ber > 0:
                    d = ber - prior_er
                    vs_prior = f" vs prior: {'+' if d >= 0 else ''}{d:.1f}kg e1RM"
                else:
                    vs_prior = ""

                flag_str  = f"  [FLAG: {', '.join(flags_s)}]" if flags_s else ""
                ex_lines.append(
                    f"    {ex_title}: {bwt}kg x {breps}r x {len(norm_sets)} sets"
                    f"  (e1RM {ber:.1f}kg){vs_prior}{flag_str}"
                )

            for line in ex_lines[:6]:
                w(line)
            if len(ex_lines) > 6:
                w(f"    ... and {len(ex_lines)-6} more exercises")
            w()

    # 4-week volume trend
    w("  4-WEEK VOLUME TREND")
    w("  " + "-" * 62)
    labels       = ["Wk -3", "Wk -2", "Wk -1", "This wk"]
    max_vol_bar  = max(bucket_vol) if any(v > 0 for v in bucket_vol) else 1
    for b in range(4):
        lbl   = labels[b]
        dlbl  = bucket_label(b)
        vol   = bucket_vol[b]
        n     = bucket_sessions[b]
        blen  = int(vol / max_vol_bar * 20) if max_vol_bar > 0 else 0
        bstr  = "#" * blen + "." * (20 - blen)
        w(f"  {lbl} ({dlbl}): [{bstr}] {vol:>10,.0f} kg*reps  {n} sess")
    w()

    # ════════════════════════════════════════════════════════════
    # SECTION 3: STRENGTH
    # ════════════════════════════════════════════════════════════
    w()
    w("=" * 72)
    w("3. STRENGTH — HOW ARE THE LIFTS MOVING?")
    w("=" * 72)
    w()
    w("  e1RM = estimated 1-rep max  (formula: weight x (1 + reps / 30))")
    w("  [C] = compound lift  |  [I] = isolation")
    w()

    def sort_ex(title):
        return (0 if is_compound(title) else 1, title.lower())

    for ex_title in sorted(ex_this_week.keys(), key=sort_ex):
        sets_list = ex_this_week[ex_title]
        if not sets_list:
            continue

        best_s    = max(sets_list, key=lambda s: s["e1rm"])
        best_wt   = best_s["wt"]
        best_reps = best_s["reps"]
        best_er   = best_s["e1rm"]

        # Prior best
        prior_list   = ex_prior.get(ex_title, [])
        prior_best   = max(prior_list, key=lambda s: s["e1rm"]) if prior_list else None
        prior_er     = prior_best["e1rm"] if prior_best else 0
        prior_date   = prior_best["date"] if prior_best else ""
        delta        = best_er - prior_er if prior_er > 0 and best_er > 0 else 0

        if prior_er > 0 and best_er > 0:
            if delta > 0.5:   comparison = f"UP +{delta:.1f}kg vs {prior_date}"
            elif delta < -0.5: comparison = f"DOWN {delta:.1f}kg vs {prior_date}"
            else:             comparison = f"SAME as {prior_date}"
        elif prior_er == 0:
            comparison = "First time in 30-day log"
        else:
            comparison = "No prior data"

        # Next session target
        if delta > 0:
            next_wt = best_wt + (2.5 if is_compound(ex_title) else 1.25)
        elif delta < -0.5:
            next_wt = round(best_wt * 0.95, 2)
        else:
            next_wt = best_wt
        next_reps = best_reps

        # Flags
        flags_ex = []
        rseq = [s["reps"] for s in sets_list]
        if len(rseq) >= 2 and rseq[0] > 0 and rseq[-1] < rseq[0] * 0.7:
            flags_ex.append(f"rep collapse ({rseq[0]}->{rseq[-1]})")
        if any(s["wt"] == 0 and s["reps"] > 0 for s in sets_list):
            flags_ex.append("0kg logged — check entry")
        wseq = [s["wt"] for s in sets_list if s["wt"] > 0]
        if len(wseq) >= 2 and wseq[-1] < wseq[0] * 0.9:
            flags_ex.append(f"weight drop ({wseq[0]}kg->{wseq[-1]}kg)")

        cmp = "[C]" if is_compound(ex_title) else "[I]"
        w(f"  {cmp} {ex_title}")
        w(f"      Best this week : {best_wt}kg x {best_reps} reps  (e1RM {best_er:.1f}kg)")
        w(f"      vs prior       : {comparison}")
        w(f"      Next session   : {next_wt}kg x {next_reps} reps")
        if flags_ex:
            w(f"      *** FLAGS: {', '.join(flags_ex)}")
        w()

    # ════════════════════════════════════════════════════════════
    # SECTION 4: MUSCLE BALANCE
    # ════════════════════════════════════════════════════════════
    w()
    w("=" * 72)
    w("4. ARE THE RIGHT MUSCLES GETTING ENOUGH WORK?")
    w("=" * 72)
    w()
    w("  Muscle Group    | Sets this wk | Target/wk | Gap    | Status")
    w("  ----------------+--------------+-----------+--------+--------")

    for m, target in MUSCLE_TARGETS.items():
        actual = sets_by_muscle_week.get(m, 0)
        gap    = target - actual
        status = "OK" if gap <= 0 else ("LOW" if gap <= 3 else "CRITICAL")
        label  = m.replace("_", " ").title()
        w(f"  {label:<16}| {actual:>12} | {target:>9} | {gap:>6} | {status}")

    w()

    # Push vs pull
    push_muscles = {"chest", "shoulders", "triceps"}
    pull_muscles = {"back", "biceps", "rear_delts", "traps"}
    push_sets = sum(sets_by_muscle_week.get(m, 0) for m in push_muscles)
    pull_sets = sum(sets_by_muscle_week.get(m, 0) for m in pull_muscles)
    p_ratio   = pull_sets / push_sets if push_sets > 0 else 0
    w(f"  Push sets: {push_sets}  |  Pull sets: {pull_sets}  |  "
      f"Ratio pull:push = {p_ratio:.2f}  "
      f"({'OK -- balanced' if p_ratio >= 1.0 else 'LOW -- add more pulling work'})")
    w()

    w(f"  Rear delts: {rd_sets} sets this week  (need 8+/week)")
    if rd_sets < 8:
        w(f"    SHORT by {8-rd_sets} sets. Rear delts stabilise the shoulder joint. "
          f"If front shoulder muscles stay much stronger than rear, you risk rotator cuff "
          f"problems over time. Add face pulls or reverse flys.")
    else:
        w("    OK -- shoulder balance maintained.")

    tr_act = sets_by_muscle_week.get("traps", 0)
    w(f"  Traps     : {tr_act} sets this week  (need 6+/week)")
    if tr_act < 6:
        w(f"    SHORT by {6-tr_act} sets. Traps support neck and upper back posture. "
          f"Add shrugs or deadlifts.")
    else:
        w("    OK.")
    w()

    ok_muscles    = [m for m, t in MUSCLE_TARGETS.items() if sets_by_muscle_week.get(m, 0) >= t]
    short_muscles = [m for m, t in MUSCLE_TARGETS.items() if sets_by_muscle_week.get(m, 0) < t]
    if ok_muscles:
        w(f"  Enough work this week: {', '.join(m.replace('_',' ').title() for m in ok_muscles)}")
    if short_muscles:
        w(f"  Short this week      : {', '.join(m.replace('_',' ').title() for m in short_muscles)}")
        w("  Under-trained muscles lose size first on a calorie deficit. "
          "Prioritise these next session.")
    w()

    # ════════════════════════════════════════════════════════════
    # SECTION 5: REST AND RECOVERY
    # ════════════════════════════════════════════════════════════
    w()
    w("=" * 72)
    w("5. REST AND RECOVERY THIS WEEK")
    w("=" * 72)
    w()

    w(f"  Sessions this week : {sess_count} of 5 target")
    for b in range(3):
        w(f"  {labels[b]} ({bucket_label(b)}): {bucket_sessions[b]} sessions")
    w()

    # Gaps between consecutive sessions this week
    if len(this_week) >= 2:
        w("  Time between sessions this week:")
        for i in range(len(this_week) - 1):
            dt1 = parse_ts(this_week[i])
            dt2 = parse_ts(this_week[i + 1])
            if not dt1 or not dt2:
                continue
            gap_hrs  = (dt2 - dt1).total_seconds() / 3600
            d1s      = dt1.astimezone(IST).strftime("%a %d %b %H:%M")
            d2s      = dt2.astimezone(IST).strftime("%a %d %b %H:%M")
            m1       = session_muscles(this_week[i])
            m2       = session_muscles(this_week[i + 1])
            overlap  = m1 & m2
            flag_p   = ""
            if gap_hrs < 24 and overlap:
                flag_p = (f"  [FLAG: only {gap_hrs:.0f}h rest, "
                          f"same muscles: {', '.join(sorted(overlap))}]")
            elif gap_hrs < 16:
                flag_p = f"  [FLAG: only {gap_hrs:.0f}h rest]"
            w(f"    {d1s} -> {d2s}: {gap_hrs:.0f}h{flag_p}")
        w()

    # Late-night sessions
    late_sessions = [
        wk for wk in this_week
        if (lambda dt: dt is not None and 0 <= dt.astimezone(IST).hour < 4)(parse_ts(wk))
    ]
    if late_sessions:
        w(f"  Sessions after midnight IST this week: {len(late_sessions)}")
        w()
        w("  WHY THIS MATTERS:")
        w("  Working out after midnight raises cortisol (the stress hormone). Cortisol")
        w("  suppresses growth hormone, which your body releases mostly during deep sleep.")
        w("  At age 44, growth hormone is already 60-70% lower than your 20s -- late sessions")
        w("  cut it further. This slows both fat loss and muscle repair. Aim for 6-9 PM IST.")
        w()
        for wk in late_sessions:
            dt = parse_ts(wk)
            if dt:
                di = dt.astimezone(IST)
                w(f"    - {di.strftime('%A %d %b %Y  %H:%M IST')}  ({wk.get('title','Workout')})")
    else:
        w("  No sessions after midnight IST this week. Good.")
    w()

    # Back-to-back same-muscle groups
    btb_lines = []
    for i in range(len(this_week) - 1):
        dt1 = parse_ts(this_week[i])
        dt2 = parse_ts(this_week[i + 1])
        if not dt1 or not dt2:
            continue
        gap_hrs = (dt2 - dt1).total_seconds() / 3600
        if gap_hrs >= 48:
            continue
        overlap = session_muscles(this_week[i]) & session_muscles(this_week[i + 1])
        if overlap:
            d1 = dt1.astimezone(IST).strftime("%a %d %b")
            d2 = dt2.astimezone(IST).strftime("%a %d %b")
            btb_lines.append(
                f"    {d1} + {d2} ({gap_hrs:.0f}h apart): overlap = {', '.join(sorted(overlap))}"
            )

    if btb_lines:
        w("  Back-to-back sessions hitting the same muscle group:")
        for line in btb_lines:
            w(line)
        w()
        w("  At age 44, muscles need 48-72h to fully repair between sessions.")
        w("  Training a muscle before it has recovered adds fatigue, not stimulus,")
        w("  and raises injury risk. Rearrange sessions to respect the recovery window.")
    else:
        w("  No back-to-back same-muscle sessions this week. Good.")
    w()

    # ════════════════════════════════════════════════════════════
    # SECTION 6: BODY RECOMPOSITION CHECK
    # ════════════════════════════════════════════════════════════
    w()
    w("=" * 72)
    w("6. BODY RECOMPOSITION CHECK")
    w("=" * 72)
    w()

    w(f"  Calorie target : {TARGET_CALS} kcal/day")
    w(f"  TDEE estimate  : {TDEE} kcal/day  (your estimated daily burn at current weight)")
    w(f"  Daily deficit  : {TDEE - TARGET_CALS} kcal  "
      f"(15% cut -- sustainable rate for muscle retention)")
    w(f"  Protein target : {PROTEIN_G}g/day  (2g per kg bodyweight)")
    w()
    w("  WHY PROTEIN MATTERS ON A CUT:")
    w("  In a calorie deficit, the body looks for extra fuel. If protein is low, it breaks")
    w("  down muscle tissue for energy -- this is called muscle catabolism. At 174g/day,")
    w("  you supply enough amino acids to maintain muscle while losing fat. Going below")
    w("  ~120g/day on this deficit risks losing the muscle you are training to build.")
    w()

    # MEV table
    w("  MUSCLE STIMULUS CHECK  (minimum sets/week to retain muscle on a calorie deficit):")
    w(f"  {'Muscle':<16} {'This wk':>8}  {'Min':>5}  Status")
    w(f"  {'-'*16} {'-'*8}  {'-'*5}  {'-'*10}")
    at_risk = []
    for m, mev in MEV.items():
        actual = sets_by_muscle_week.get(m, 0)
        status = "OK" if actual >= mev else "AT RISK"
        label  = m.replace("_", " ").title()
        w(f"  {label:<16} {actual:>8}  {mev:>5}  {status}")
        if actual < mev:
            at_risk.append(label)
    w()
    if at_risk:
        w(f"  Muscles at risk of loss this week (below minimum stimulus):")
        w(f"    {', '.join(at_risk)}")
        w("  These are not getting enough signal to hold on to muscle during a deficit.")
        w("  Add sets for these in the next 1-2 sessions.")
    else:
        w("  All muscle groups above minimum effective volume this week. Good.")
    w()

    # Deload timing
    week_count   = state.get("week_count", 0)
    last_counted = state.get("last_counted_week")
    this_week_str = today_ist.strftime("%Y-W%W")
    if last_counted != this_week_str and sess_count > 0:
        week_count += 1
        state["week_count"]        = week_count
        state["last_counted_week"] = this_week_str

    last_deload_week   = state.get("last_deload_week", 0)
    weeks_since_deload = week_count - last_deload_week
    next_deload_in     = max(0, DELOAD_EVERY_N_WEEKS - weeks_since_deload)
    next_deload_date   = (today_ist + timedelta(weeks=next_deload_in)).strftime("%d %b %Y")

    w(f"  Active training weeks logged : {week_count}")
    w(f"  Weeks since last deload      : {weeks_since_deload}  "
      f"(deload every {DELOAD_EVERY_N_WEEKS} weeks)")
    if next_deload_in == 0:
        w("  *** DELOAD THIS WEEK ***")
        w("      Cut all sets to 2 per exercise. Keep weights the same.")
        w("      Deload weeks let joints and connective tissue recover.")
        w("      You will come back stronger after the deload.")
    else:
        w(f"  Next deload : in {next_deload_in} week(s), approx {next_deload_date}")
    w()

    # ── Write file ──
    content = "\n".join(lines) + "\n"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(content)

    section("ANALYSIS REPORT — Sections 1-6 complete")
    print(f"\n  Report date : {report_date}")
    print(f"  This week   : {sess_count} sessions")
    print(f"  Prior weeks : {prior_counts[0]}, {prior_counts[1]}, {prior_counts[2]}")
    print(f"  Saved ->    : {report_file}")

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
    "analysis":    run_analysis_report,
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
