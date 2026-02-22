# coding: utf-8
"""
------------------------------------------------------------------------------
Copyright 2026 Michael Ryan Hunsaker
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
 http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
------------------------------------------------------------------------------
"""

import json
import random
import argparse
import csv
import copy
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import List, Dict, Set, Any, Optional, Union

"""
Workout Generator Module
========================
This module automates the creation of progressive weekly workout plans.

Core Logic Systems
------------------
1. FATIGUE TRACKING:
   The script calculates a 'fatigue score' for every exercise based on how
   frequently it appeared in the previous week. This ensures variety by
   deprioritizing recently used movements.

2. SELECTION ALGORITHM:
   Exercises are selected by filtering the library for a specific body region
   (Upper, Lower, or Core) and then sorting the results by their fatigue score.
   The script randomly picks from the bottom 50% of the fatigue-sorted list to
   balance variety with randomness.

3. PROGRESSIVE OVERLOAD (3-MONTH):
   When generating a 3-month block the script produces 13 weeks (≈ 3 months)
   of workouts. Weights are increased at the start of each new week by the
   per-exercise increment stored in the library field "weekly_increment"
   (defaults to 2.5 lbs for most exercises, 5.0 lbs for primary compound
   lower-body movements). Bodyweight exercises are never incremented.

4. WORKOUT ARCHITECTURE:
   Workouts are generated using 'Valid Combinations' of set types (Regular,
   Ladder, and AMSAP). This ensures the training volume is balanced and
   adheres to specific time constraints.

5. RUNNING:
   An optional running session can be appended to each day. The running
   library now includes explicit FARTLEK variants (Build Speed, Steady,
   Sprint Intervals) as well as Tempo and Easy runs. When --addrun is
   passed a session is drawn from this pool per day.

6. EXCEPTION HANDLING:
   Uses a CSV-based mapping to dynamically skip exercises and suggest
   replacements during the generation phase without altering the master library.

7. PDF CONVERSION:
   Invokes 'pandoc' via a system subprocess to transform the Markdown output
   into a professionally formatted PDF using the xelatex engine.

Constants
---------
LIBRARY_FILE : str
    Master JSON database of all available exercises.
PREVIOUS_WEEK_FILE : str
    JSON log of the previous week used to calculate fatigue.
EXCEPTIONS_FILE : str
    CSV file mapping exercises to be skipped and their replacements.
DEFAULT_WEIGHT_INCREMENT : float
    Standard poundage added during weight progression (2.5 lbs).
SET_TYPES : List[str]
    The three supported set formats: Regular, Ladder, and AMSAP.
TIME_CAPS : Dict[str, int]
    Mapping of set types to their recommended time limits in minutes.
WEEKS_PER_BLOCK : int
    Number of weeks generated when --three-months flag is used (13 ≈ 3 months).
"""

# --- Configuration Constants ---
LIBRARY_FILE: str = "exercise_library.json"
PREVIOUS_WEEK_FILE: str = "previous_week.json"
EXCEPTIONS_FILE: str = "exceptions.csv"
DEFAULT_WEIGHT_INCREMENT: float = 2.5
SET_TYPES: List[str] = ["regular", "ladder", "amsap"]
TIME_CAPS: Dict[str, int] = {"regular": 20, "ladder": 30, "amsap": 30}
RUNNING_FILE: str = "running.json"
WEEKS_PER_BLOCK: int = 13  # ≈ 3 months

# Exercises whose default increment should be 5 lbs (primary compound movers)
HEAVY_INCREMENT_PATTERNS: List[str] = [
    "hip_extension", "hip_hinge", "unilateral_squat", "squat",
    "explosive_squat", "split_squat", "lateral_squat", "unilateral_extension",
    "horizontal_push", "vertical_push", "horizontal_pull", "vertical_pull",
]

# Valid workout combinations (full ~60-min workout)
VALID_COMBINATIONS_FULL: List[List[str]] = [
    ["regular", "regular", "amsap"],
    ["regular", "regular", "ladder"],
    ["regular", "amsap", "regular"],
    ["regular", "ladder", "regular"],
    ["amsap", "regular", "regular"],
    ["ladder", "regular", "regular"],
    ["amsap", "ladder"],
    ["ladder", "amsap"],
]

# Valid workout combinations (short ~30-min workout)
VALID_COMBINATIONS_SHORT: List[List[str]] = [
    ["regular", "regular"],
    ["amsap"],
    ["ladder"],
]

TYPICAL_ROUNDS: Dict[str, int] = {
    "regular": 5,
    "ladder": 7,
    "amsap": 10,
}


# ---------------------------------------------------------------------------
# Running library helpers
# ---------------------------------------------------------------------------

BUILTIN_RUNNING: List[Dict[str, Any]] = [
    {
        "id": "fartlek-build",
        "name": "FARTLEK: Build Speed",
        "instruction": (
            "Warm up 5 min easy. Then alternate: 1 min hard effort (RPE 8-9) / "
            "2 min easy jog (RPE 4-5). Increase the hard effort by 30 sec each "
            "round until you reach 3 min hard. Cool down 5 min easy. Total ~45-60 min."
        ),
        "equipment": ["outdoors", "manual treadmill", "flat treadmill"],
        "category": "fartlek",
    },
    {
        "id": "fartlek-steady",
        "name": "FARTLEK: Steady State",
        "instruction": (
            "Warm up 5 min easy. Run at a comfortably hard pace (RPE 6-7) for "
            "6 min, then drop to an easy jog for 4 min. Repeat 4-6 rounds. "
            "Cool down 5 min easy. Total ~55-65 min."
        ),
        "equipment": ["outdoors", "manual treadmill", "flat treadmill"],
        "category": "fartlek",
    },
    {
        "id": "fartlek-sprint",
        "name": "FARTLEK: Sprint Intervals",
        "instruction": (
            "Warm up 10 min easy. Sprint at 90-95% effort for 20-30 sec, "
            "then walk or jog very easy for 90 sec. Complete 8-12 sprint rounds. "
            "Cool down 10 min easy. Total ~35-50 min."
        ),
        "equipment": ["outdoors", "manual treadmill", "flat treadmill"],
        "category": "fartlek",
    },
    {
        "id": "fartlek-pyramid",
        "name": "FARTLEK: Pyramid",
        "instruction": (
            "Warm up 5 min. Hard efforts: 1 min, 2 min, 3 min, 4 min, 3 min, "
            "2 min, 1 min — with equal recovery jog between each. "
            "Cool down 5 min easy. Total ~45 min."
        ),
        "equipment": ["outdoors", "manual treadmill", "flat treadmill"],
        "category": "fartlek",
    },
    {
        "id": "tempo",
        "name": "Tempo Run",
        "instruction": (
            "Warm up 10 min easy. Run at threshold pace (RPE 7-8, can speak only "
            "a few words) for 20-30 min. Cool down 10 min easy. Total ~45-50 min."
        ),
        "equipment": ["outdoors", "manual treadmill", "flat treadmill"],
        "category": "tempo",
    },
    {
        "id": "easy-run",
        "name": "Easy Recovery Run",
        "instruction": (
            "Run at a conversational pace (RPE 4-5) for 30-45 min. "
            "Focus on relaxed form and breathing. No need to push pace."
        ),
        "equipment": ["outdoors", "manual treadmill", "flat treadmill"],
        "category": "easy",
    },
]


def load_running() -> List[Dict[str, Any]]:
    """Load running exercises, merging file-based entries with built-ins."""
    path: Path = Path(RUNNING_FILE)
    if path.exists():
        data = json.loads(path.read_text())
        file_exercises = data.get("exercises", [])
        # Merge: built-ins first, file entries override by id
        merged: Dict[str, Any] = {ex["id"]: ex for ex in BUILTIN_RUNNING}
        for ex in file_exercises:
            merged[ex["id"]] = ex
        return list(merged.values())
    return list(BUILTIN_RUNNING)


# ---------------------------------------------------------------------------
# Weight progression helpers
# ---------------------------------------------------------------------------

def _weekly_increment_for(exercise: Dict[str, Any], override: Optional[float] = None) -> float:
    """Return the per-week weight increment for an exercise.

    Rules (in priority order):
    1. If the exercise specifies a ``weekly_increment`` field, use that.
    2. If a user override is provided via CLI, use that.
    3. If the exercise's movement pattern matches a heavy-lift pattern, use 5.0.
    4. Otherwise use DEFAULT_WEIGHT_INCREMENT (2.5).
    Bodyweight exercises always return 0.
    """
    if exercise.get("units") == "bodyweight":
        return 0.0
    if "weekly_increment" in exercise:
        return float(exercise["weekly_increment"])
    if override is not None:
        return float(override)
    if exercise.get("movement_pattern", "") in HEAVY_INCREMENT_PATTERNS:
        return 5.0
    return DEFAULT_WEIGHT_INCREMENT


def apply_weight_progression(
    library: List[Dict[str, Any]],
    weeks_elapsed: int = 1,
    override: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Return a deep-copied library with loads incremented by `weeks_elapsed` weeks."""
    progressed = copy.deepcopy(library)
    for ex in progressed:
        if ex.get("units") == "bodyweight":
            continue
        inc = _weekly_increment_for(ex, override)
        ex["default_load"] = round(ex.get("default_load", 0.0) + inc * weeks_elapsed, 2)
    return progressed


def apply_weight_progression_file(library_file: str, increment: float) -> bool:
    """Persist a single-week weight increment to the library JSON file (original behaviour)."""
    path: Path = Path(library_file)
    if not path.exists():
        return False
    library: List[Dict[str, Any]] = json.loads(path.read_text())
    for ex in library:
        if ex.get("units") == "bodyweight":
            continue
        ex["default_load"] = round(ex.get("default_load", 0.0) + increment, 2)
    path.write_text(json.dumps(library, indent=2))
    return True


# ---------------------------------------------------------------------------
# Library / data loaders
# ---------------------------------------------------------------------------

def load_library() -> List[Dict[str, Any]]:
    """Load the master exercise list from the local JSON file."""
    return json.loads(Path(LIBRARY_FILE).read_text())


def load_previous() -> List[Dict[str, Any]]:
    """Load data from the previous week to assist in fatigue calculations."""
    path: Path = Path(PREVIOUS_WEEK_FILE)
    if path.exists():
        return json.loads(path.read_text())
    return []


def load_exceptions() -> Dict[str, str]:
    """Load exercise exclusions and replacements from a CSV file."""
    exceptions: Dict[str, str] = {}
    path: Path = Path(EXCEPTIONS_FILE)
    if path.exists():
        with open(path, "r") as f:
            reader: csv.DictReader = csv.DictReader(f)
            for row in reader:
                exceptions[row["exercise"].strip()] = row["replacement"].strip()
    return exceptions


def apply_exceptions(
    exercises: List[Dict[str, Any]], exceptions: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Filter out excluded exercises from the available pool."""
    if not exceptions:
        return exercises
    filtered: List[Dict[str, Any]] = []
    for ex in exercises:
        key_match = ex.get("id") in exceptions or ex.get("name") in exceptions
        if key_match:
            key = ex.get("id") if ex.get("id") in exceptions else ex.get("name")
            print(f"Excluding: {ex['id']} (replacement: {exceptions.get(key)})")
            continue
        filtered.append(ex)
    return filtered


# ---------------------------------------------------------------------------
# Core selection logic
# ---------------------------------------------------------------------------

def fatigue_map(previous: List[Dict[str, Any]]) -> Dict[Union[str, int], float]:
    """Create a frequency-based weight map for exercise selection."""
    f: Dict[Union[str, int], float] = defaultdict(float)
    for e in previous:
        rounds: int = e.get("completed_rounds", 0)
        multiplier: float = 1.0 + (min(rounds, 10) / 10.0)
        f[e["exercise_id"]] += multiplier
    return f


def select(
    pool: List[Dict[str, Any]],
    used: Set[Union[str, int]],
    fatigue: Dict[Union[str, int], float],
    day_excluded: Optional[Set[Union[str, int]]] = None,
) -> Dict[str, Any]:
    """Select the next exercise using a fatigue-weighted randomized approach."""
    if day_excluded is None:
        day_excluded = set()
    available: List[Dict[str, Any]] = [
        e for e in pool if e["id"] not in used and e["id"] not in day_excluded
    ]
    if not available:
        raise ValueError(
            "Pool exhausted for selection. Check library size or region filters."
        )
    available.sort(key=lambda e: fatigue[e["id"]])
    ex: Dict[str, Any] = random.choice(available[: max(1, len(available) // 2)])
    used.add(ex["id"])
    return ex


def region_filter(
    exercises: List[Dict[str, Any]], region: str, ladder_only: bool
) -> List[Dict[str, Any]]:
    """Filter the exercise pool by body region and format compatibility."""
    return [
        e
        for e in exercises
        if region in e["body_regions"] and (not ladder_only or e["ladder_eligible"])
    ]


# ---------------------------------------------------------------------------
# Week generation
# ---------------------------------------------------------------------------

def generate_week(
    exercises: List[Dict[str, Any]],
    previous: List[Dict[str, Any]],
    days: int,
    short_workout: bool = False,
    add_run: bool = False,
    fatigue: Optional[Dict[Union[str, int], float]] = None,
) -> List[Dict[str, Any]]:
    """Generate a single training week.

    Parameters
    ----------
    exercises : list
        The exercise library (already weight-adjusted for this week).
    previous : list
        Previous-week tracking data used to seed the fatigue map.
    days : int
        Number of training days to generate.
    short_workout : bool
        Use short (≈30-min) combination templates.
    add_run : bool
        Append a running session to each day.
    fatigue : dict, optional
        An existing fatigue map to carry across multi-week generation.
        If None a fresh map is built from `previous`.

    Returns
    -------
    list
        Structured week data (list of day dicts).
    """
    if fatigue is None:
        fatigue = fatigue_map(previous)

    running_pool = load_running() if add_run else []
    week: List[Dict[str, Any]] = []
    combinations = VALID_COMBINATIONS_SHORT if short_workout else VALID_COMBINATIONS_FULL
    run_duration = 30 if short_workout else 60

    for d in range(1, days + 1):
        used: Set[Union[str, int]] = set()
        day_struct: Dict[str, Any] = {"day": d, "sets": []}
        day_excluded: Set[Union[str, int]] = set()
        selected_combination: List[str] = random.choice(combinations)

        for st in selected_combination:
            ladder_only: bool = st in ["ladder", "amsap"]

            upper = select(region_filter(exercises, "upper", ladder_only), used, fatigue, day_excluded)
            day_excluded.add(upper["id"])
            for exid in upper.get("exclusion", []):
                day_excluded.add(exid)

            lower = select(region_filter(exercises, "lower", ladder_only), used, fatigue, day_excluded)
            day_excluded.add(lower["id"])
            for exid in lower.get("exclusion", []):
                day_excluded.add(exid)

            core = select(region_filter(exercises, "core", ladder_only), used, fatigue, day_excluded)
            day_excluded.add(core["id"])
            for exid in core.get("exclusion", []):
                day_excluded.add(exid)

            rounds: int = TYPICAL_ROUNDS.get(st, 0)
            multiplier: float = 1.0 + (min(rounds, 10) / 10.0)
            for ex in (upper, lower, core):
                fatigue[ex["id"]] += multiplier

            day_struct["sets"].append(
                {
                    "set_type": st,
                    "time_cap_min": TIME_CAPS[st],
                    "round_scheme": (
                        "AMSAP" if st == "amsap"
                        else "10-1 ladder" if st == "ladder"
                        else "5 rounds"
                    ),
                    "exercises": [upper, lower, core],
                }
            )

        if add_run and running_pool:
            run_ex = random.choice(running_pool)
            day_struct["sets"].append(
                {
                    "set_type": "running",
                    "time_cap_min": run_duration,
                    "round_scheme": f"{run_duration} Minutes",
                    "exercises": [run_ex],
                }
            )

        week.append(day_struct)

    return week


# ---------------------------------------------------------------------------
# 3-month block generation
# ---------------------------------------------------------------------------

def generate_three_month_block(
    base_exercises: List[Dict[str, Any]],
    previous: List[Dict[str, Any]],
    days: int,
    short_workout: bool = False,
    add_run: bool = False,
    weight_increment_override: Optional[float] = None,
    start_date: Optional[date] = None,
    weeks: int = WEEKS_PER_BLOCK,
) -> List[Dict[str, Any]]:
    """Generate `weeks` consecutive training weeks with progressive weight increases.

    Each week the exercise library loads are incremented according to the
    per-exercise rules:
      - Bodyweight exercises: no change.
      - Primary compound lower / upper movements: +5.0 lbs/week.
      - All other weighted exercises: +2.5 lbs/week (or override value).

    Parameters
    ----------
    base_exercises : list
        The exercise library at Week 1 load levels.
    previous : list
        Previous-week data (fatigue seeding).
    days : int
        Training days per week.
    short_workout : bool
        Use short combination templates.
    add_run : bool
        Append a running session each day.
    weight_increment_override : float, optional
        Override the default per-exercise increment logic with a single value.
    start_date : date, optional
        The Monday that Week 1 starts. Defaults to next Monday.
    weeks : int
        Total weeks to generate (default 13).

    Returns
    -------
    list of dict
        Each element represents one week::

            {
                "week_number": int,          # 1-indexed
                "start_date": str,           # ISO date of Monday
                "exercises": list,           # library snapshot used this week
                "days": list,               # day structures from generate_week()
            }
    """
    if start_date is None:
        start_date = next_monday()

    fatigue = fatigue_map(previous)
    block: List[Dict[str, Any]] = []

    for week_num in range(1, weeks + 1):
        week_start = start_date + timedelta(weeks=week_num - 1)

        # Apply cumulative weight increase relative to base (week_num - 1 increments)
        week_exercises = apply_weight_progression(
            base_exercises,
            weeks_elapsed=week_num - 1,
            override=weight_increment_override,
        )

        week_days = generate_week(
            week_exercises,
            previous,
            days,
            short_workout=short_workout,
            add_run=add_run,
            fatigue=fatigue,  # carry fatigue across weeks
        )

        block.append(
            {
                "week_number": week_num,
                "start_date": week_start.isoformat(),
                "exercises": week_exercises,
                "days": week_days,
            }
        )

    return block


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def render_json_week(week_days: List[Dict[str, Any]], day_offset: int = 0) -> List[Dict[str, Any]]:
    """Flatten one week's day structures into tracking rows."""
    rows: List[Dict[str, Any]] = []
    for day in week_days:
        for s in day["sets"]:
            set_type: str = s["set_type"]
            rounds: int = 1 if set_type == "running" else TYPICAL_ROUNDS.get(set_type, 0)
            for ex in s["exercises"]:
                rows.append(
                    {
                        "day": day["day"] + day_offset,
                        "exercise_id": ex["id"],
                        "exercise_name": ex["name"],
                        "set_type": set_type,
                        "completed_rounds": rounds,
                    }
                )
    return rows


def _render_set(s: Dict[str, Any], set_index: int) -> List[str]:
    """Render a single set block to markdown lines."""
    out: List[str] = []
    out.append(f"### Set {set_index} — {s['set_type'].upper()}")
    if s["set_type"] == "regular":
        out.append(f"**{s['round_scheme'].upper()}**: 5 ☐ 4 ☐ 3 ☐ 2 ☐ 1 ☐")
    elif s["set_type"] == "ladder":
        out.append(
            f"**{s['round_scheme'].upper()}**: "
            "10 ☐ 9 ☐ 8 ☐ 7 ☐ 6 ☐ 5 ☐ 4 ☐ 3 ☐ 2 ☐ 1 ☐"
        )
    elif s["set_type"] == "amsap":
        out.append(
            f"**{s['round_scheme'].upper()}**: "
            "Repeat this set for 30 minutes. No Need to Count ☐"
        )
    elif s["set_type"] == "running":
        out.append(f"**DURATION**: {s['round_scheme']} ☐")

    for ex in s["exercises"]:
        if s["set_type"] == "running":
            out.append(f"- **{ex['name']}**")
            out.append(f"**Instruction**: {ex['instruction']}   ")
            out.append(f"**Equipment Needed**: {', '.join(ex['equipment'])}   ")
        else:
            load_display = (
                "Bodyweight"
                if ex.get("units") == "bodyweight"
                else f"{ex['default_load']} pounds   "
            )
            out.append(
                f"- {ex['name']} | {load_display} | {ex['reps']} {ex['reptype']}   "
            )
            out.append(f"**Muscle Groups**:  {', '.join(ex['muscle_groups'])}   ")
            out.append(f"**Equipment Needed**: {', '.join(ex['equipment'])}   ")
        out.append("")
    return out


REMARKBOX_SNIPPET = """## Leave a Comment

Note, I use [Remarkbox](https://www.remarkbox.com/) for comments to prevent Disqus from showing ads or other methods requiring a GitHub login for participation in any discussions. Although you are asked for your email, there is no need to verify it through remarkbox in order to leave a comment. Verification is just so you can track discussions, etc. without the system treating you as a new person every time.

<!-- Remarkbox - Your readers want to communicate with you -->
<div id="remarkbox-div">
    <noscript>
        <iframe id=remarkbox-iframe src="https://my.remarkbox.com/embed?nojs=true&mode=light" style="height:600px;width:100%;border:none!important" tabindex=0></iframe>
    </noscript>
</div>
<script src="https://my.remarkbox.com/static/js/iframe-resizer/iframeResizer.min.js"></script>
<script>
    var rb_owner_key = "9f6d3e72-e739-11f0-b88e-040140774501";
    var thread_uri = window.location.href;
    var thread_title = window.document.title;
    var thread_fragment = window.location.hash;

    var rb_src = "https://my.remarkbox.com/embed" +
            "?rb_owner_key=" + rb_owner_key +
            "&thread_title=" + encodeURI(thread_title) +
            "&thread_uri=" + encodeURIComponent(thread_uri) +
            "&mode=light" +
            thread_fragment;

    function create_remarkbox_iframe() {
        var ifrm = document.createElement("iframe");
        ifrm.setAttribute("id", "remarkbox-iframe");
        ifrm.setAttribute("scrolling", "no");
        ifrm.setAttribute("src", rb_src);
        ifrm.setAttribute("frameborder", "0");
        ifrm.setAttribute("tabindex", "0");
        ifrm.setAttribute("title", "Remarkbox");
        ifrm.style.width = "100%";
        document.getElementById("remarkbox-div").appendChild(ifrm);
    }
    create_remarkbox_iframe();
    iFrameResize(
        {
            checkOrigin: ["https://my.remarkbox.com"],
            inPageLinks: true,
            initCallback: function(e) {e.iFrameResizer.moveToAnchor(thread_fragment)}
        },
        document.getElementById("remarkbox-iframe")
    );
</script>"""


def render_md_week(
    week_days: List[Dict[str, Any]],
    week_number: int,
    start_date_str: str,
    append_remarkbox: bool = True,
) -> str:
    """Render a single week to a Markdown string."""
    out: List[str] = [
        f"# Training Week {week_number}",
        f"*Week starting {start_date_str}*",
        "",
    ]
    for day in week_days:
        out.append(f"## Day {day['day']}")
        for i, s in enumerate(day["sets"], 1):
            out.extend(_render_set(s, i))
    if append_remarkbox:
        out.append(REMARKBOX_SNIPPET)
    return "\n".join(out)


def render_md_block(block: List[Dict[str, Any]]) -> str:
    """Render an entire 3-month block into a single Markdown document."""
    sections: List[str] = [
        "# 3-Month Training Block",
        f"*Generated {datetime.now().date().isoformat()}*  ",
        f"*{len(block)} weeks of progressive programming*",
        "",
    ]
    for week_data in block:
        sections.append(
            render_md_week(
                week_data["days"],
                week_data["week_number"],
                week_data["start_date"],
                append_remarkbox=False,
            )
        )
        sections.append("\n---\n")
    sections.append(REMARKBOX_SNIPPET)
    return "\n".join(sections)


def render_md_single(
    week: List[Dict[str, Any]], generated_date: Optional[date] = None
) -> str:
    """Convert a single-week day list into a human-readable Markdown string (legacy)."""
    gen_date: date = generated_date if generated_date is not None else datetime.now().date()
    out: List[str] = ["# Training Week", f"*Generated {gen_date}*", ""]
    for day in week:
        out.append(f"## Day {day['day']}")
        for i, s in enumerate(day["sets"], 1):
            out.extend(_render_set(s, i))
    out.append(REMARKBOX_SNIPPET)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def next_monday(from_dt: Optional[datetime] = None) -> date:
    """Return the date of the next Monday (or the Monday 7 days ahead if today is Monday)."""
    if from_dt is None:
        from_dt = datetime.now()
    weekday: int = from_dt.weekday()
    days_ahead: int = (0 - weekday) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (from_dt + timedelta(days=days_ahead)).date()


# ---------------------------------------------------------------------------
# Post / Jekyll helpers
# ---------------------------------------------------------------------------

def write_post_copy(
    md_text: str, start_date: date, posts_dir: Optional[str] = None
) -> Path:
    """Write a Jekyll _posts copy with YAML front matter."""
    if posts_dir is None:
        repo_root: Path = Path(__file__).resolve().parent.parent
        p: Path = repo_root / "_posts"
    else:
        p = Path(posts_dir)
    p.mkdir(parents=True, exist_ok=True)
    fname: str = f"{start_date.strftime('%Y-%m-%d')}-workout.md"
    fm: List[str] = [
        "---",
        f'title: "Workout for week starting {start_date.strftime("%Y-%m-%d")}"',
        'excerpt_separator: "<!--more-->"',
        f'permalink: /blog/workout/{start_date.strftime("%Y-%m-%d")}/',
        f"date: {start_date.strftime('%Y-%m-%d')}",
        "toc: true",
        "categories:",
        "  - blog",
        "tags:",
        "  - workout plan",
        "comments: true",
        "share: true",
        "read_time: true",
        "related: true",
        f"last_updates_at: {start_date.strftime('%Y-%m-%d')}",
        "---",
        "",
    ]
    content: str = "\n".join(fm) + md_text
    path: Path = p / fname
    path.write_text(content)
    print(f"Post copy saved: {path}")
    return path


def write_block_posts(block: List[Dict[str, Any]], posts_dir: Optional[str] = None) -> None:
    """Write one Jekyll post per week in a 3-month block."""
    for week_data in block:
        start = date.fromisoformat(week_data["start_date"])
        md = render_md_week(
            week_data["days"],
            week_data["week_number"],
            week_data["start_date"],
            append_remarkbox=True,
        )
        write_post_copy(md, start, posts_dir)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def convert_to_pdf(md_file: str, pdf_file: str) -> bool:
    """Invoke Pandoc to convert Markdown to PDF."""
    try:
        subprocess.run(
            ["pandoc", md_file, "-o", pdf_file],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"PDF generated: {pdf_file}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        error_msg: str = getattr(e, "stderr", "Pandoc not found in PATH")
        print(f"PDF conversion failed: {error_msg}")
        return False


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Execution entry point for the Workout Generator."""
    ap = argparse.ArgumentParser(description="Progressive Workout Generator")
    ap.add_argument("--days", type=int, default=5, help="Training days per week")
    ap.add_argument("--sets-per-day", type=int, default=3, help="Sets per day (informational)")
    ap.add_argument("--seed", type=int, help="Random seed for reproducible schedules")
    ap.add_argument("--md", default="generated_week.md", help="Markdown output filename")
    ap.add_argument("--json", default="generated_week.json", help="JSON tracking filename")
    ap.add_argument("--pdf", action="store_true", help="Generate PDF (requires pandoc)")
    ap.add_argument("--short", action="store_true", help="Use short (~30-min) workout templates")
    ap.add_argument("--skip", action="store_true", help="Filter via exceptions.csv")
    ap.add_argument("--add-weight", action="store_true", help="Increment loads in library file")
    ap.add_argument(
        "--weight-increment",
        type=float,
        default=None,
        help=(
            "Override per-week lb increment (default: 2.5 accessory / 5.0 compound). "
            "Setting this applies the same value to all weighted exercises."
        ),
    )
    ap.add_argument(
        "--three-months",
        action="store_true",
        help=(
            "Generate a full 3-month (13-week) block. Outputs one combined Markdown "
            "file and one JSON file, plus individual Jekyll _posts per week."
        ),
    )
    ap.add_argument(
        "--weeks",
        type=int,
        default=WEEKS_PER_BLOCK,
        help="Number of weeks when using --three-months (default 13)",
    )
    ap.add_argument(
        "--addrun",
        action="store_true",
        help="Append a random running session (incl. FARTLEK variants) to each day",
    )
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Persist a one-time weight bump to the library file if requested
    if args.add_weight:
        inc = args.weight_increment if args.weight_increment is not None else DEFAULT_WEIGHT_INCREMENT
        apply_weight_progression_file(LIBRARY_FILE, inc)
        print()

    exercises: List[Dict[str, Any]] = load_library()
    if args.skip:
        exceptions = load_exceptions()
        if exceptions:
            exercises = apply_exceptions(exercises, exceptions)

    previous_data = load_previous()
    start_date: date = next_monday(datetime.now())

    # ------------------------------------------------------------------
    # 3-month block mode
    # ------------------------------------------------------------------
    if args.three_months:
        print(f"Generating {args.weeks}-week training block starting {start_date} …")
        block = generate_three_month_block(
            base_exercises=exercises,
            previous=previous_data,
            days=args.days,
            short_workout=args.short,
            add_run=args.addrun,
            weight_increment_override=args.weight_increment,
            start_date=start_date,
            weeks=args.weeks,
        )

        # Combined Markdown
        md_filename = args.md.replace(".md", "_3month.md") if ".md" in args.md else f"{args.md}_3month.md"
        md_content = render_md_block(block)
        Path(md_filename).write_text(md_content)
        print(f"3-month Markdown saved: {md_filename}")

        # Combined JSON (flat tracking rows for all weeks)
        json_filename = args.json.replace(".json", "_3month.json") if ".json" in args.json else f"{args.json}_3month.json"
        all_rows: List[Dict[str, Any]] = []
        for week_data in block:
            rows = render_json_week(week_data["days"])
            for row in rows:
                row["week_number"] = week_data["week_number"]
                row["week_start"] = week_data["start_date"]
            all_rows.extend(rows)
        Path(json_filename).write_text(json.dumps(all_rows, indent=2))
        print(f"3-month JSON saved: {json_filename}")

        # Individual Jekyll posts
        try:
            write_block_posts(block)
        except Exception as e:
            print(f"Failed to write some post copies: {e}")

        # Save the last week as previous_week.json for future progression
        last_week_rows = render_json_week(block[-1]["days"])
        Path(PREVIOUS_WEEK_FILE).write_text(json.dumps(last_week_rows, indent=2))
        print(f"Previous week updated: {PREVIOUS_WEEK_FILE}")

        if args.pdf:
            pdf_name = f"workout_3month_{datetime.now().strftime('%Y%m%d')}.pdf"
            convert_to_pdf(md_filename, pdf_name)

        return

    # ------------------------------------------------------------------
    # Single-week mode (original behaviour)
    # ------------------------------------------------------------------
    week = generate_week(
        exercises,
        previous_data,
        args.days,
        short_workout=args.short,
        add_run=args.addrun,
    )

    md_content = render_md_single(week, generated_date=start_date)
    Path(args.md).write_text(md_content)
    print(f"Markdown saved: {args.md}")

    try:
        write_post_copy(md_content, start_date)
    except Exception as e:
        print(f"Failed to write post copy: {e}")

    tracking_rows = render_json_week(week)
    Path(args.json).write_text(json.dumps(tracking_rows, indent=2))
    print(f"Tracking data saved: {args.json}")

    if args.pdf:
        pdf_name = f"workout_{datetime.now().strftime('%Y%m%d')}.pdf"
        convert_to_pdf(args.md, pdf_name)


if __name__ == "__main__":
    main()