# Progressive Workout Generator

A Python-based workout generator that creates intelligent, progressive 45-60 minute workouts with smart exercise pairing and complementary muscle group targeting.

## Overview

This system generates 5-day workout weeks with:

- **3 sets per day** (each ~12-20 minutes)
- **2-3 exercises per set** depending on day type
- **5 rounds per set** before moving to the next set
- **Automatic week-to-week progression** (2.5% load increase by default)
- **Smart exercise pairing** - exercises complement each other
- **A/B week rotation** with varied exercise selection
- **Ladder days** (Day 2 & 4) with alternating ground/standing exercises
- **JSON-based workflow** for clean data persistence and progression tracking

## Key Training Principles

### Regular Days (Days 1, 3, 5)

**3-exercise sets when possible:**

1. First exercise works specific muscle groups (ground-based)
2. Second exercise works complementary muscle groups (standing)
3. Third exercise (integration) uses muscles from exercises 1 & 2

**Example:** 

- Exercise 1: Hamstring curl (ground, posterior chain)
- Exercise 2: Front squat (standing, anterior chain + core)
- Exercise 3: Clam walk with strap (integration using core + lower body stabilization)

**2-exercise sets when integration unavailable:**

- Just lower body + upper body pairing

### Ladder Days (Days 2 & 4)

**Always 2 exercises alternating ground/standing:**

- One lower body exercise (ground-based)
- One upper body exercise (standing)
- Ladder format: 10 reps each, then 9, then 8... down to 1
- Explicitly labeled with [GROUND] and [STANDING] tags

**Example:**

```
[GROUND] Hamstring Curl (Slider) ↔ [STANDING] Standing Row
Do 10 curls, 10 rows, 9 curls, 9 rows, 8 curls, 8 rows... down to 1 each
```

## Quick Start

### Prerequisites

- Python 3.7 or higher
- No external libraries required (uses only standard library)

### Installation

1. Download all files to a folder:

```bash
your-workout-folder/
├── workout_generator.py
├── exercise_library.json
├── exceptions.csv (optional)
├── add_exercise.sh (optional helper)
└── README.md
```

2. Run the generator:

```bash
python3 workout_generator.py
```

3. Two files will be created:
   - `generated_week.json` - Machine-readable workout data for progression tracking
   - `generated_week.md` - Human-readable workout card with checkboxes

### Week-to-Week Progression

The new JSON workflow makes progression simple and automatic:

```bash
# After completing your week, run the helper script:
bash nextWeek.sh

# Or do it manually:
# 1. Archive your completed week
mkdir -p progress
cp generated_week.json "progress/week_$(date +%Y%m%d).json"

# 2. Set up for progression
mv generated_week.json previous_week.json

# 3. Generate next week with automatic 2.5% load increase
python3 workout_generator.py
```

The system will:

- Automatically increase loads by 2.5% from your previous week
- Select different exercises to avoid repetition
- Switch between A/B week patterns
- Track your progression history in JSON format

### Custom Progression & Injury Exceptions

```bash
# Increase loads by 5% instead of default 2.5%
python3 workout_generator.py --increase 5%

# Use injury exceptions from exceptions.csv
python3 workout_generator.py --exception

# Combine both
python3 workout_generator.py --increase 5% --exception
```

**Setting up exceptions.csv:**

```csv
exercise,replacement
Bulgarian Split Squat,Lunge (Forward or Back)
Jump Squat,Goblet Front Squat
```

## Workout Structure

### Weekly Pattern

```
Monday (Day 1):    Regular - 3 sets × 3 exercises × 5 rounds
Tuesday (Day 2):   LADDER - 3 sets × 2 exercises × 5 rounds
Wednesday (Day 3): Regular - 3 sets × 3 exercises × 5 rounds  
Thursday (Day 4):  LADDER - 3 sets × 2 exercises × 5 rounds
Friday (Day 5):    Regular - 3 sets × 3 exercises × 5 rounds
```

### Regular Day Example (Day 1, Set 1)

```
Set 1 - 5 Rounds
├─ Exercise 1: Hamstring Curl [ground] (10-12 reps)
├─ Exercise 2: Sumo Squat [standing] (10-12 reps)  
└─ Exercise 3: Front Squat - Integration (10-12 reps)

Complete all 3 exercises, rest 60-90 sec, repeat 5x total
```

### Ladder Day Example (Day 2, Set 1)

```
Set 1 - (Ladder Format)
├─ [GROUND] Hamstring Curl: 10-9-8-7-6-5-4-3-2-1
└─ [STANDING] Frontline POW Raise: 10-9-8-7-6-5-4-3-2-1

Alternate: 10 curls, 10 raises, 9 curls, 9 raises... down to 1 each
Complete entire ladder
```

## Understanding the Output

### Markdown File (`generated_week.md`)

The markdown file includes built-in progress tracking with checkboxes:

**Regular Day:**

```markdown
## Day 1 (Regular Day)
### Set 1
#### Repeats: 5 [ ] 4 [ ] 3 [ ] 2 [ ] 1 [ ]

**1 Hamstring Curl (Yoga Ball)** 
10-12 reps | Load: Bodyweight — Primer/Alt

**2 Sumo Squat** 
10-12 reps | Load: 45.0 lbs — Primer/Alt

**3 Front Squat (Goblet)** 
10-12 reps | Load: 45.0 lbs — Integration
```

**Ladder Day:**

```markdown
## Day 2 (Ladder Day)
### Set 1
#### Ladder: 10 [ ] 9 [ ] 8 [ ] 7 [ ] 6 [ ] 5 [ ] 4 [ ] 3 [ ] 2 [ ] 1 [ ]

**[GROUND] Hamstring Curl (Yoga Ball)** 
Ladder 10-1 reps | Load: Bodyweight — Primer/Alt

**[STANDING] Frontline POW Raise** 
Ladder 10-1 reps | Load: 45.0 lbs — Primer/Alt
```

### JSON File Structure (`generated_week.json`)

The JSON file stores complete workout data for progression tracking:

```json
[
  {
    "week_type": "B",
    "day": 1,
    "set": 1,
    "rounds": 5,
    "is_ladder": false,
    "set_duration": 30.0,
    "exercise_id": "hamstring_yoga_ball_curl",
    "exercise_name": "Hamstring Curl (Yoga Ball)",
    "position": "ground",
    "reps": "10-12",
    "load": 0.0,
    "notes": "Primer/Alt",
    "total_day_duration": 30.0
  }
]
```

**Key fields:**

- `week_type`: A or B (alternates weekly)
- `exercise_id`: Used for progression tracking across weeks
- `load`: Current weight in lbs (automatically increased week-to-week)
- `is_ladder`: Boolean indicating ladder format
- `position`: Ground or standing (critical for ladder days)

## Exercise Library Requirements

### JSON Structure

Exercises are defined in `exercise_library.json`:

```json
{
  "id": "goblet_front_squat",
  "name": "Front Squat (Goblet)",
  "body_regions": ["lower"],
  "movement_pattern": "squat",
  "plane_of_motion": "sagittal",
  "roles": ["primary_lower", "integration"],
  "ladder_eligible": true,
  "ground_or_standing": "standing",
  "equipment": ["dumbbell", "kettlebell"]
}
```

### Required Fields

| Field                | Type    | Description                                          |
| -------------------- | ------- | ---------------------------------------------------- |
| `id`                 | string  | Unique identifier (used for progression tracking)    |
| `name`               | string  | Display name                                         |
| `body_regions`       | array   | ["lower", "upper", "core", "arms", "shoulder", etc.] |
| `movement_pattern`   | string  | Type of movement (squat, hinge, push, pull, etc.)    |
| `plane_of_motion`    | string  | sagittal, frontal, transverse, or multi              |
| `roles`              | array   | Exercise categories (see below)                      |
| `ladder_eligible`    | boolean | Can this be used in ladder format?                   |
| `ground_or_standing` | string  | "ground" or "standing"                               |
| `equipment`          | array   | Required equipment (or empty for bodyweight)         |

### Exercise Roles Explained

- **primary_lower**: Main lower body movements (squats, lunges, step-ups)
- **primary_upper**: Main upper body (rows, presses, pull-ups)
- **posterior_chain**: Hamstrings/glutes focused (curls, hip thrusts, bridges)
- **integration**: Complex movements using multiple muscle groups (Copenhagen plank, loaded carries, complex stabilization)
- **accessory**: Isolation or supplementary work (curls, raises, rotator cuff work)

### Ground vs Standing

Critical for ladder days and exercise pairing:

- **ground**: Floor-based exercises (push-ups, planks, slider curls, bridges)
- **standing**: Upright exercises (squats, rows, overhead press, lunges)

Ladder days alternate these positions to manage fatigue and allow continuous work.

## Adding New Exercises

### Method 1: Manual JSON Editing

Add directly to `exercise_library.json`:

```json
{
  "id": "deficit_push_up",
  "name": "Deficit Push Up",
  "body_regions": ["upper", "core"],
  "movement_pattern": "horizontal_push",
  "plane_of_motion": "sagittal",
  "roles": ["primary_upper"],
  "ladder_eligible": true,
  "ground_or_standing": "ground",
  "equipment": ["yoga_block"]
}
```

### Method 2: Using the Helper Script

The included `add_exercise.sh` script provides an interactive way to add exercises:

```bash
bash add_exercise.sh
```

You'll be prompted for:

- Exercise name
- Exercise ID (lowercase, underscores)
- Body regions (comma-separated)
- Roles (comma-separated)
- Equipment (comma-separated)
- Ladder eligible (true/false)
- Position (ground/standing)

**Requirements:** The script uses `jq` for JSON manipulation. Install with:

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

## Customization

### Adjusting Workout Parameters

Edit these constants in `workout_generator.py`:

```python
WORKOUT_DAYS = 5          # Days per week
SETS_PER_DAY = 3          # Sets per workout day
ROUNDS_PER_SET = 5        # Times through each set
```

**Example customization:**

- For shorter workouts: `ROUNDS_PER_SET = 3`
- For more variety: `SETS_PER_DAY = 4`
- For 6-day program: `WORKOUT_DAYS = 6`

### Default Load Assignment

The system assigns starting loads based on equipment:

```python
def get_base_load(exercise):
    eq = exercise.get("equipment", [])
    if "dumbbell" in eq: return 10.0
    if "kettlebell" in eq: return 10.0
    return 0.0  # Bodyweight
```

Modify these values to match your starting strength level.

## Integration Exercise Design

For 3-exercise sets to work optimally, integration exercises should:

1. **Use multiple muscle groups** from the first two exercises
2. **Challenge stability and coordination** 
3. **Be appropriate as a "finisher"** for the set

**Good integration examples:**

- Copenhagen Plank (adductors + obliques + core stability)
- Clam Walk with Strap (glutes + hip stabilizers + core)
- March in Place with Strap (core anti-rotation + hip flexors)
- Front Squat (legs + core + upper back stabilization)

**What makes integration work:**
The first two exercises prepare/fatigue specific muscle groups, then the integration exercise requires those same muscles to work together in a complex pattern.

## Week Type (A/B Rotation)

Automatically alternates based on calendar week number:

- **Odd weeks** (1, 3, 5, etc.) = **Week A**
- **Even weeks** (2, 4, 6, etc.) = **Week B**

This creates natural exercise variety without manual tracking. The week type is stored in the JSON output for reference.

## Understanding Progression

### How It Works

1. **First week**: Uses default loads (10 lbs for weighted, bodyweight for others)
2. **Subsequent weeks**: Reads `previous_week.json` and increases loads

```python
def calculate_progression(exercise_id, previous_data, increase_str):
    """Calculate load progression using the provided increase percentage."""
    if exercise_id not in previous_data:
        return None
    multiplier = 1 + (float(increase_str.replace("%", "")) / 100)
    # Average all instances of this exercise from previous week
    loads = [float(r["load"]) for r in previous_data[exercise_id]]
    return round((sum(loads) / len(loads)) * multiplier, 1)
```

### Example Progression

Week 1: Goblet Squat @ 10.0 lbs
Week 2: Goblet Squat @ 10.3 lbs (10.0 × 1.025)
Week 3: Goblet Squat @ 10.5 lbs (10.3 × 1.025)
Week 4: Goblet Squat @ 10.8 lbs (10.5 × 1.025)

### Why JSON vs CSV?

The previous CSV format had limitations:

- Hard to parse complex nested data
- No support for metadata
- Difficult to track exercise relationships
- Manual string parsing required

**JSON advantages:**

- Native Python support (no external libraries)
- Preserves data types (numbers, booleans, arrays)
- Easy to query by `exercise_id` for progression
- Clean integration with modern tools
- Human-readable when formatted

## Tips for Best Results

### Execution

1. **Warm-up**: 5-10 minutes of light cardio and dynamic stretching
2. **Rest between rounds**: 60-90 seconds for regular sets, 90-120 seconds for ladders
3. **Form over speed**: Perfect technique on every rep
4. **Breathing**: Exhale on exertion, inhale on return
5. **Check boxes**: Mark off completed rounds in the markdown file

### Programming

1. **Consistency**: Train 5 days/week
2. **Rest days**: Full rest or light activity on weekends
3. **Sleep**: 7-9 hours for recovery
4. **Nutrition**: Align calories with your goals (surplus for building, maintenance for recomp)
5. **Deload**: Every 4-6 weeks, reduce loads by 30-40% or take a full rest week

### Progress Tracking

The `nextWeek.sh` script automatically archives your progress:

```bash
bash nextWeek.sh
```

This creates:

```
progress/
├── week_20241224.json
├── week_20241231.json
└── week_20250107.json
```

You can analyze progression over time by comparing these JSON files.

## Troubleshooting

### "Not enough exercises selected"

**Cause:** Insufficient exercises in library for the selection criteria

**Solution:** Add more exercises to `exercise_library.json`, especially:

- Lower body movements (primary_lower role)
- Upper body movements (primary_upper role)
- Integration exercises
- Mix of ground and standing positions

### "No complementary exercises found"

**Cause:** Limited integration exercises available

**Solution:** This is normal behavior. The system will create 2-exercise sets instead. To enable more 3-exercise sets, add exercises with the "integration" role that use multiple body regions.

### Workouts feel too short/long

**Solution:** Adjust `ROUNDS_PER_SET`:

- Too short? Increase to 6-7 rounds
- Too long? Decrease to 3-4 rounds

### Same exercises every week

**Solution:** The A/B week rotation provides some variety, but for more diversity:

1. Expand your exercise library with more options per category
2. Add exercises with similar roles but different movement patterns
3. Consider manually curating a larger pool

### Load not increasing

**Check:**

1. Does `previous_week.json` exist?
2. Are `exercise_id` values consistent in your library?
3. Run with verbose output: `python3 workout_generator.py --increase 2.5%`

### Helper script not working

**Cause:** Missing `jq` dependency

**Fix:**

```bash
# macOS
brew install jq

# Ubuntu/Debian  
sudo apt-get install jq

# Or manually add to JSON without the script
```

## File Structure

```
.
├── workout_generator.py       # Main generator script
├── exercise_library.json      # Exercise database  
├── exceptions.csv             # Optional injury replacements
├── add_exercise.sh            # Optional helper script
├── nextWeek.sh                # Progression automation script
├── generated_week.json        # Output: machine-readable, used for progression
├── generated_week.md          # Output: human-readable with checkboxes
├── previous_week.json         # Auto-created: last week's data for progression
├── progress/                  # Auto-created: archived weeks
│   ├── week_20241224.json
│   └── week_20241231.json
└── README.md                  # This file
```

## Sample Weekly Schedule

```
Monday:    Day 1 (Regular) - ~45-60 minutes
Tuesday:   Day 2 (Ladder) - ~40-50 minutes
Wednesday: Day 3 (Regular) - ~45-60 minutes
Thursday:  Day 4 (Ladder) - ~40-50 minutes
Friday:    Day 5 (Regular) - ~45-60 minutes
Saturday:  Active recovery (walk, yoga, light cardio)
Sunday:    Full rest
```

## Advanced: Understanding the Selection Algorithm

### Regular Day Set Building

1. **Select integration target**: Choose randomly from exercises with "integration" role
2. **Find complementary exercises**: 
   - Filter for ground-based exercises sharing body regions with target
   - Filter for standing exercises sharing body regions with target
3. **Assign positions**:
   - Exercise 1: Ground exercise (prepares specific muscles)
   - Exercise 2: Standing exercise (prepares complementary muscles)
   - Exercise 3: Integration exercise (uses both sets of muscles)

### Ladder Day Set Building

1. **Select lower body**: Choose from ground-based, ladder-eligible, lower body movements
2. **Select upper body**: Choose from standing, ladder-eligible, upper body movements
3. **Label clearly**: [GROUND] and [STANDING] tags for easy execution

### Avoiding Repetition

- `used_today` set tracks exercises already selected for current day
- Different exercises are chosen for each set
- A/B week rotation provides variety across weeks
- Progression tracking via `exercise_id` ensures consistent development

## Sharing & Customization

This system is designed to be easily shared and modified:

### Sharing with Training Partners

1. **Share the basics:**

   ```bash
   # Core files only
   workout_generator.py
   exercise_library.json
   README.md
   ```

2. **Share with your customizations:**

   ```bash
   # Include your exercise library
   workout_generator.py
   exercise_library.json (your expanded version)
   exceptions.csv (if using)
   README.md
   ```

3. **Share with progression history:**

   ```bash
   # Everything including your progress
   workout_generator.py
   exercise_library.json
   generated_week.json
   generated_week.md
   progress/
   README.md
   ```

### Creating Exercise Library Variants

Consider creating specialized versions:

- `exercise_library_home.json` - Minimal equipment
- `exercise_library_gym.json` - Full gym access
- `exercise_library_rehab.json` - Modified for injury recovery

Switch between them by editing `LIBRARY_JSON` constant in the script.

## Contributing

If you create useful exercises or improvements:

1. Document your additions in JSON format
2. Include notes on equipment requirements
3. Specify appropriate roles and positions
4. Share your customizations with the community

## License

Free to use, modify, and share. Credit appreciated but not required.

---

**Progressive overload through intelligent exercise pairing and clean JSON-based progression tracking. Train smarter, not just harder.**

---

## CLI Usage

The program supports the following command-line arguments:

| Argument         | Description                                           | Default Value       |
| ---------------- | ----------------------------------------------------- | ------------------- |
| `--days`         | Number of days to generate workouts for               | 5                   |
| `--sets-per-day` | Number of sets per day                                | 3                   |
| `--seed`         | Random seed for reproducible results                  | None                |
| `--md`           | Output file for the generated week in Markdown format | generated_week.md   |
| `--json`         | Output file for the generated week in JSON format     | generated_week.json |

### Example Commands

1. **Generate a default 5-day workout week:**

   ```bash
   python workout_generator.py
   ```

2. **Generate a 3-day workout week with 2 sets per day:**

   ```bash
   python workout_generator.py --days 3 --sets-per-day 2
   ```

3. **Generate a reproducible 5-day workout week using a specific seed:**

   ```bash
   python workout_generator.py --seed 42
   ```

4. **Generate a 5-day workout week and save the output to custom files:**

   ```bash
   python workout_generator.py --md my_week.md --json my_week.json
   ```

---

## How It Works

### Workout Generation Logic

- **Valid Combinations:** The workout can be generated as:
  - 2 regular sets and an AMSAP or ladder,
  - an AMSAP and a ladder.
- **Prohibited:** An AMSAP, a ladder, and a regular set cannot appear together in the same day.
- **Duration:** Each workout is limited to 60 minutes, with AMSAP and Ladders set to 30 minutes each.

### Exercise Selection

1. **Select lower body:** Choose from ground-based, ladder-eligible, lower body movements
2. **Select upper body:** Choose from standing, ladder-eligible, upper body movements
3. **Label clearly:** [GROUND] and [STANDING] tags for easy execution

### Avoiding Repetition

- `used_today` set tracks exercises already selected for the current day
- Different exercises are chosen for each set
- A/B week rotation provides variety across weeks
- Progression tracking via `exercise_id` ensures consistent development

---

## License

This is available on an Apache 2.0 license. 
---

