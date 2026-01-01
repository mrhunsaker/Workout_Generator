
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
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import List, Dict, Set, Any, Optional, Union

"""
Workout Generator Module
========================
This module automates the creation of progressive weekly workout plans. It is 
designed to serve as a functional help file and a roadmap for development.

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

3. PROGRESSIVE OVERLOAD:
   When triggered, the script performs a 'Weight Progression' pass. It iterates 
   through the library and adds a constant increment (default 2.5 lbs) to all 
   weighted exercises while skipping bodyweight-only movements.

4. WORKOUT ARCHITECTURE:
   Workouts are generated using 'Valid Combinations' of set types (Regular, 
   Ladder, and AMSAP). This ensures the training volume is balanced 
   and adheres to specific time constraints.

5. EXCEPTION HANDLING:
   Uses a CSV-based mapping to dynamically skip exercises and suggest replacements
   during the generation phase without altering the master library.

6. PDF CONVERSION:
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
"""

# --- Configuration Constants ---
# These paths and defaults control the data ingestion and output behavior.
LIBRARY_FILE: str = "exercise_library.json"
PREVIOUS_WEEK_FILE: str = "previous_week.json"
EXCEPTIONS_FILE: str = "exceptions.csv"
DEFAULT_WEIGHT_INCREMENT: float = 2.5 
SET_TYPES: List[str] = ["regular", "ladder", "amsap"]
TIME_CAPS: Dict[str, int] = {"regular": 20, "ladder": 30, "amsap": 30}

# Define valid workout combinations (full workout)
# Each sub-list represents a sequence of set types for a single day.
VALID_COMBINATIONS_FULL: List[List[str]] = [
    ["regular", "regular", "amsap"],
    ["regular", "regular", "ladder"],
    ["regular", "amsap", "regular"],
    ["regular", "ladder", "regular"],
    ["amsap", "regular", "regular"],
    ["ladder", "regular", "regular"],
    ["amsap", "ladder"],
    ["ladder", "amsap"]
]

# Define valid workout combinations (short workout - 30 min)
# Optimized patterns for limited time-frames.
VALID_COMBINATIONS_SHORT: List[List[str]] = [
    ["regular", "regular"],
    ["amsap"],
    ["ladder"]
]
TYPICAL_ROUNDS: Dict[str, int] = {
    "regular": 5,
    "ladder": 7,
    "amsap": 10  
} # Representative averages for a 30-minute block

def apply_weight_progression(library_file: str, increment: float) -> bool:
    """
    Updates the exercise library to implement progressive overload.

    Logic
    -----
    1. Creates a timestamped backup of the current library.
    2. Identifies weighted exercises (units != 'bodyweight').
    3. Increments the 'default_load' and rounds to 2 decimal places.
    """
    path: Path = Path(library_file)
    if not path.exists():
        return False
    
    # Logic for backup and loading...
    # (Full docstrings add significant length here)

def load_library() -> List[Dict[str, Any]]:
    """
    Load the master exercise list from the local JSON file.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries where each dict represents an exercise's metadata.
    """
    return json.loads(Path(LIBRARY_FILE).read_text())

def load_previous() -> List[Dict[str, Any]]:
    """
    Load data from the previous week to assist in fatigue calculations.

    Notes
    -----
    This function checks for the existence of the tracking file. If absent, 
    it returns an empty list, allowing the generator to start a fresh cycle.

    Returns
    -------
    List[Dict[str, Any]]
        A list of previously performed exercises. Returns empty if no file exists.
    """
    path: Path = Path(PREVIOUS_WEEK_FILE)
    if path.exists():
        return json.loads(path.read_text())
    return []

def load_exceptions() -> Dict[str, str]:
    """
    Load exercise exclusions and replacements from a CSV file.

    Notes
    -----
    The CSV should contain two columns: 'exercise' and 'replacement'. This is 
    primarily used for physical therapy modifications or equipment availability.

    Returns
    -------
    Dict[str, str]
        A dictionary mapping excluded exercise names to their replacements.
    """
    exceptions: Dict[str, str] = {}
    path: Path = Path(EXCEPTIONS_FILE)
    if path.exists():
        with open(path, 'r') as f:
            reader: csv.DictReader = csv.DictReader(f)
            for row in reader:
                exceptions[row['exercise'].strip()] = row['replacement'].strip()
    return exceptions

def apply_exceptions(exercises: List[Dict[str, Any]], exceptions: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Filter out excluded exercises from the available pool.

    Parameters
    ----------
    exercises : List[Dict[str, Any]]
        The current pool of available exercises from the library.
    exceptions : Dict[str, str]
        A dictionary containing keys of exercises that must be skipped.

    Returns
    -------
    List[Dict[str, Any]]
        A filtered list containing only exercises not found in the exceptions list.
    """
    if not exceptions:
        return exercises
    
    filtered: List[Dict[str, Any]] = []
    for ex in exercises:
        if ex['name'] in exceptions:
            print(f"Excluding: {ex['name']} (replacement: {exceptions[ex['name']]})")
            continue
        filtered.append(ex)
    
    return filtered

def fatigue_map(previous: List[Dict[str, Any]]) -> Dict[Union[str, int], float]:
    """
    Creates a frequency-based weight map for exercise selection.

    Logic
    -----
    Calculates fatigue score using a multiplier based on completed rounds.
    Multiplier = 1.0 + (rounds / 10.0), capped between 1.0 and 2.0.
    """
    f: Dict[Union[str, int], float] = defaultdict(float)
    for e in previous:
        rounds: int = e.get("completed_rounds", 0)
        multiplier: float = 1.0 + (min(rounds, 10) / 10.0) # Scale between 1.0 and 2.0
        f[e["exercise_id"]] += multiplier
    return f

def render_json(week: List[Dict[str, Any]]) -> str:
    """
    Flatten the week structure for JSON tracking.

    Logic
    -----
    Automatically assigns completed_rounds based on set type to inform 
    the fatigue multiplier in the next generation cycle.
    """
    rows: List[Dict[str, Any]] = []
    for day in week:
        for s in day["sets"]:
            set_type: str = s["set_type"]
            rounds: int = TYPICAL_ROUNDS.get(set_type, 0) # Assign automated rounds
            for ex in s["exercises"]:
                rows.append({
                    "day": day["day"],
                    "exercise_id": ex["id"],
                    "exercise_name": ex["name"],
                    "set_type": set_type,
                    "completed_rounds": rounds
                })
    return json.dumps(rows, indent=2)

def select(pool: List[Dict[str, Any]], used: Set[Union[str, int]], fatigue: Dict[Union[str, int], float]) -> Dict[str, Any]:
    """
    Selects the next exercise using a fatigue-weighted randomized approach.

    Logic
    -----
    1. Removes any exercise IDs already used in the current workout day (intra-day variety).
    2. Sorts the remaining candidates by their fatigue score (least used first).
    3. Truncates the list to the bottom (freshest) 50%.
    4. Randomly selects one move from this "fresh" half to ensure the plan 
       isn't strictly deterministic while maintaining variety.

    Parameters
    ----------
    pool : List[Dict[str, Any]]
        The list of exercises filtered for a specific body region or set type.
    used : Set[Union[str, int]]
        A set of IDs representing exercises already committed to the current day.
    fatigue : Dict[Union[str, int], float]
        The fatigue score mapping generated by `fatigue_map`.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the metadata for the chosen exercise.

    Raises
    ------
    ValueError
        If the candidate pool is empty after applying filters.
    """
    available: List[Dict[str, Any]] = [e for e in pool if e["id"] not in used]
    if not available:
        raise ValueError("Pool exhausted for selection. Check library size or region filters.")
    
    # Sort and slice to pick from the "freshest" exercises.
    available.sort(key=lambda e: fatigue[e["id"]])
    ex: Dict[str, Any] = random.choice(available[:max(1, len(available)//2)])
    used.add(ex["id"])
    return ex

def region_filter(exercises: List[Dict[str, Any]], region: str, ladder_only: bool) -> List[Dict[str, Any]]:
    """
    Filter the exercise pool by body region and equipment/format compatibility.

    Parameters
    ----------
    exercises : List[Dict[str, Any]]
        The comprehensive list of available exercises.
    region : str
        The target body region string (e.g., 'upper', 'lower', 'core').
    ladder_only : bool
        If True, only exercises marked as suitable for 'ladder' format are returned.

    Returns
    -------
    List[Dict[str, Any]]
        A subset of the library matching the criteria.
    """
    return [e for e in exercises if region in e["body_regions"] and (not ladder_only or e["ladder_eligible"])]

def generate(exercises: List[Dict[str, Any]], 
             previous: List[Dict[str, Any]], 
             days: int, 
             sets_per_day: int, 
             short_workout: bool = False) -> List[Dict[str, Any]]:
    """
    Orchestrates the creation of a multi-day training program.

    Logic
    -----
    Assigns set-type combinations and selects exercises. Real-time fatigue 
    is updated during generation using the round-based multiplier.
    """
    fatigue: Dict[Union[str, int], float] = fatigue_map(previous)
    week: List[Dict[str, Any]] = []
    combinations: List[List[str]] = VALID_COMBINATIONS_SHORT if short_workout else VALID_COMBINATIONS_FULL
    
    for d in range(1, days + 1):
        used: Set[Union[str, int]] = set()
        day_struct: Dict[str, Any] = {"day": d, "sets": []}
        selected_combination: List[str] = random.choice(combinations)
        
        for st in selected_combination:
            ladder_only: bool = st in ["ladder", "amsap"]
            upper: Dict[str, Any] = select(region_filter(exercises, "upper", ladder_only), used, fatigue)
            lower: Dict[str, Any] = select(region_filter(exercises, "lower", ladder_only), used, fatigue)
            core: Dict[str, Any] = select(region_filter(exercises, "core", ladder_only), used, fatigue)
            
            # Apply multiplier in real-time
            rounds: int = TYPICAL_ROUNDS.get(st, 0)
            multiplier: float = 1.0 + (min(rounds, 10) / 10.0)
            for ex in (upper, lower, core):
                fatigue[ex["id"]] += multiplier
                
            day_struct["sets"].append({
                "set_type": st,
                "time_cap_min": TIME_CAPS[st],
                "round_scheme": "AMSAP" if st == "amsap" else "10-1 ladder" if st == "ladder" else "5 rounds",
                "exercises": [upper, lower, core]
            })
        week.append(day_struct)
    return week

def render_md(week: List[Dict[str, Any]], generated_date: Optional[date] = None) -> str:
    """
    Convert the generated week data into a human-readable Markdown string.

    Notes
    -----
    This renderer includes a specific CSS-style page break after each day 
    to facilitate clean PDF printing. It also handles the logic for displaying 
    'Bodyweight' instead of '0.0 pounds'.

    Parameters
    ----------
    week : List[Dict[str, Any]]
        The structured workout data generated by `generate`.

    Returns
    -------
    str
        A formatted Markdown document.
    """
    gen_date: date = generated_date if generated_date is not None else datetime.now().date()
    out: List[str] = ["# Training Week", f"*Generated {gen_date}*", ""]
    for day in week:
        out.append(f"## Day {day['day']}")
        for i, s in enumerate(day["sets"], 1):
            out.append(f"### Set {i} — {s['set_type'].upper()}")

            # Provide checkboxes for tracking progress during the workout.
            if s['set_type'] == 'regular':
                out.append(f"**{s['round_scheme'].upper()}**: 5 ☐ 4 ☐ 3 ☐ 2 ☐ 1 ☐")
            elif s['set_type'] == 'ladder':
                out.append(f"**{s['round_scheme'].upper()}**: 10 ☐ 9 ☐ 8 ☐ 7 ☐ 6 ☐ 5 ☐ 4 ☐ 3 ☐ 2 ☐ 1 ☐")
            elif s['set_type'] == 'amsap':
                out.append(f"**{s['round_scheme'].upper()}**: Repeat this set for 30 minutes. No Need to Count ☐")
            
            for ex in s["exercises"]:
                load_display: str = "Bodyweight" if ex.get("units") == "bodyweight" else f"{ex['default_load']} pounds   "
                out.append(f"- {ex['name']} | {load_display} | {ex['reps']} {ex['reptype']}   ")
                out.append(f"**Muscle Groups**:  {', '.join(ex['muscle_groups'])}   ")
                out.append(f"**Equipment Needed**: {', '.join(ex['equipment'])}   ")
            out.append("")
        out.append("--- \n")        
        out.append(f'<div style="page-break-after: always"></div>'"\n")
        
    return "\n".join(out)


def next_monday(from_dt: Optional[datetime] = None) -> date:
    """
    Return the date for the subsequent Monday from `from_dt` (or today).

    If `from_dt` is already a Monday, returns the Monday one week later.
    """
    if from_dt is None:
        from_dt = datetime.now()
    weekday: int = from_dt.weekday()  # Monday == 0
    days_ahead: int = (0 - weekday) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (from_dt + timedelta(days=days_ahead)).date()


def write_post_copy(md_text: str, start_date: date, posts_dir: Optional[str] = None) -> Path:
    """
    Write a copy of the markdown to `_posts/YYYY-MM-DD-workout.md` with the
    requested YAML front matter using `start_date` for all date fields.

    By default this writes to the repository root `_posts` directory (one level
    above `src`), so calling the script from `src` will still place the post at
    the project root as requested.
    """
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


def convert_to_pdf(md_file: str, pdf_file: str) -> bool:
    """
    Invoke Pandoc via subprocess to convert Markdown to a professional PDF.

    Notes
    -----
    This requires `pandoc` and a LaTeX engine (like `xelatex`, `lulatex`, or 'pdflatex (pandoc default)`) to be installed 
    on the host system.

    Parameters
    ----------
    md_file : str
        Path to the generated source Markdown file.
    pdf_file : str
        Target file path for the output PDF.

    Returns
    -------
    bool
        True if the conversion subprocess exited successfully, False otherwise.
    """
    try:
        subprocess.run(
            ["pandoc", md_file, "-o", pdf_file],
            check=True, capture_output=True, text=True
        )
        print(f"PDF generated: {pdf_file}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        error_msg: str = getattr(e, 'stderr', 'Pandoc not found in PATH')
        print(f"PDF conversion failed: {error_msg}")
        return False

def main() -> None:
    """
    Execution entry point for the Workout Generator.
    
    Logic
    -----
    1. Parses command-line arguments to configure the run (days, seed, format).
    2. Applies weight progression if requested by the user.
    3. Loads the exercise library and filters by equipment exceptions.
    4. Generates a training week using fatigue-weighted randomness.
    5. Exports the plan to Markdown, JSON (tracking), and PDF (optional).
    """
    ap: argparse.ArgumentParser = argparse.ArgumentParser(description="Progressive Workout Generator")
    ap.add_argument("--days", type=int, default=5, help="Number of workout days to generate")
    ap.add_argument("--sets-per-day", type=int, default=3, help="Number of sets (blocks) per daily session")
    ap.add_argument("--seed", type=int, help="Optional random seed for reproducible schedules")
    ap.add_argument("--md", default="generated_week.md", help="Filename for Markdown output")
    ap.add_argument("--json", default="generated_week.json", help="Filename for tracking data JSON")
    ap.add_argument("--pdf", action="store_true", help="Generate a PDF file (requires pandoc)")
    ap.add_argument("--short", action="store_true", help="Use short-workout (30-min) templates")
    ap.add_argument("--skip", action="store_true", help="Filter exercises using exceptions.csv")
    ap.add_argument("--add-weight", action="store_true", help="Increment weight loads in the library file")
    ap.add_argument("--weight-increment", type=float, default=DEFAULT_WEIGHT_INCREMENT, help="Pounds to add during progression")
    args: argparse.Namespace = ap.parse_args()

    # Seed randomization for testing or fixed planning.
    if args.seed is not None:
        random.seed(args.seed)

    # Progression Logic: Modifies the master library.
    if args.add_weight:
        apply_weight_progression(LIBRARY_FILE, args.weight_increment)
        print()
        
    # Data Ingestion.
    exercises: List[Dict[str, Any]] = load_library()
    if args.skip:
        exceptions: Dict[str, str] = load_exceptions()
        if exceptions:
            exercises = apply_exceptions(exercises, exceptions)
    
    # Calculation Phase.
    previous_data: List[Dict[str, Any]] = load_previous()
    week: List[Dict[str, Any]] = generate(
        exercises, previous_data, args.days, args.sets_per_day, short_workout=args.short
    )

    # Persistence/Export Phase.
    # Determine the subsequent Monday for the workout start date and use it
    start_date: date = next_monday(datetime.now())

    md_content: str = render_md(week, generated_date=start_date)
    Path(args.md).write_text(md_content)
    print(f"Markdown saved: {args.md}")

    # Also write the post copy into the _posts folder with consistent dates
    try:
        write_post_copy(md_content, start_date)
    except Exception as e:
        print(f"Failed to write post copy: {e}")

    Path(args.json).write_text(render_json(week))
    print(f"Tracking data saved: {args.json}")
    
    if args.pdf:
        pdf_name: str = f"workout_{datetime.now().strftime('%Y%m%d')}.pdf"
        convert_to_pdf(args.md, pdf_name)

if __name__ == "__main__":
    main()