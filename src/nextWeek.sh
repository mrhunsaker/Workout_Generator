#!/usr/bin/env bash
# ============================================================
# nextWeek.sh  — Workout Generator rollover wrapper
#
# Handles archiving, workspace cleanup, and then delegates
# to workout_generator.py with the correct flags.
#
# Usage:
#   bash nextWeek.sh              → interactive prompts
#   bash nextWeek.sh -3           → 3-month block, defaults
#   bash nextWeek.sh -3 --run     → block + running sessions
#   bash nextWeek.sh -3 -i 5.0   → block, 5 lb/wk override
#   bash nextWeek.sh -h           → show help
# ============================================================
set -euo pipefail

# ── Colour codes ─────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
CYAN='\033[0;36m';  BOLD='\033[1m';      NC='\033[0m'

# ── Defaults ──────────────────────────────────────────────────
THREE_MONTHS=false  # -3 / --three-months
WEEKS=13            # --weeks N
ADD_RUN=false       # --run / --addrun
SHORT=false         # --short
SKIP=false          # --skip
DAYS=5              # --days N
SEED=""             # --seed N
INC=""              # --weight-increment VALUE (empty = use built-in rules)
PDF=false           # --pdf

# ── Help ──────────────────────────────────────────────────────
usage() {
  cat <<EOF
${BOLD}nextWeek.sh${NC} — Workout Generator rollover script

${BOLD}USAGE${NC}
  bash nextWeek.sh [OPTIONS]

${BOLD}OPTIONS${NC}
  -3, --three-months         Generate a full 3-month block (default: 13 weeks)
      --weeks N              Override number of weeks in a block   [default: 13]
  -i, --increment VALUE      Override the per-week lb increment for ALL exercises
                             (leave unset to use built-in rules:
                              +5 lb/wk compound  |  +2.5 lb/wk accessory  |  0 bodyweight)
      --run                  Append a running/FARTLEK session to each day
      --short                Use short (~30-min) workout templates
      --skip                 Filter exercises listed in exceptions.csv
      --days N               Training days per week              [default: 5]
      --seed N               Random seed (reproducible output)
      --pdf                  Convert output to PDF via pandoc
  -h, --help                 Show this help and exit

${BOLD}HOW PROGRESSION WORKS${NC}
  In 3-month mode the generator automatically applies progressive overload
  across all weeks WITHOUT touching your exercise library file:
    Compound lifts  →  +5 lb / week
    Accessory work  →  +2.5 lb / week
    Bodyweight      →  unchanged
  Pass -i / --increment to override that logic with one value for every
  weighted exercise.

${BOLD}EXAMPLES${NC}
  bash nextWeek.sh -3                 # 3-month block, built-in progression
  bash nextWeek.sh -3 --run           # + running sessions each day
  bash nextWeek.sh -3 -i 5.0         # force 5 lb/wk on every exercise
  bash nextWeek.sh -3 --weeks 12     # 12-week block
  bash nextWeek.sh                    # interactive mode (single week default)
EOF
}

# ── Argument parsing ──────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    -3|--three-months)  THREE_MONTHS=true;   shift   ;;
    --weeks)            WEEKS="$2";          shift 2 ;;
    -i|--increment)     INC="$2";            shift 2 ;;
    --run|--addrun)     ADD_RUN=true;        shift   ;;
    --short)            SHORT=true;          shift   ;;
    --skip)             SKIP=true;           shift   ;;
    --days)             DAYS="$2";           shift 2 ;;
    --seed)             SEED="$2";           shift 2 ;;
    --pdf)              PDF=true;            shift   ;;
    -h|--help)          usage; exit 0        ;;
    *)
      echo -e "${YELLOW}Unknown option: $1${NC}"
      echo "Run 'bash nextWeek.sh -h' for help."
      exit 1 ;;
  esac
done

# ── Interactive mode (no flags supplied) ──────────────────────
if [[ "$THREE_MONTHS" == false && "$ADD_RUN" == false && -z "$INC" ]]; then
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}  Workout Generator — Rollover Assistant${NC}"
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo

  read -rp "Generate a 3-month (13-week) block? [Y/n] " resp
  if [[ "$resp" =~ ^[Yy]$ || -z "$resp" ]]; then
    THREE_MONTHS=true
    read -rp "Number of weeks? [default: 13] " resp
    [[ "$resp" =~ ^[0-9]+$ ]] && WEEKS="$resp"
    read -rp "Override lb increment per week? (leave blank for built-in rules) " resp
    [[ -n "$resp" ]] && INC="$resp"
  fi

  read -rp "Append a running/FARTLEK session to each day? [y/N] " resp
  [[ "$resp" =~ ^[Yy]$ ]] && ADD_RUN=true
fi

# ── Build the python argument list ────────────────────────────
PYARGS=(--days "$DAYS")

[[ "$THREE_MONTHS" == true ]] && PYARGS+=(--three-months --weeks "$WEEKS")

# NOTE: --weight-increment is an *override* only; omitting it lets the
# generator apply its built-in per-exercise rules (+5 compound / +2.5 accessory)
[[ -n "$INC"  ]] && PYARGS+=(--weight-increment "$INC")

[[ "$ADD_RUN" == true ]] && PYARGS+=(--addrun)
[[ "$SHORT"   == true ]] && PYARGS+=(--short)
[[ "$SKIP"    == true ]] && PYARGS+=(--skip)
[[ -n "$SEED" ]]         && PYARGS+=(--seed "$SEED")
[[ "$PDF"     == true ]] && PYARGS+=(--pdf)

# ── Derive expected output filenames ─────────────────────────
# Matches exactly what workout_generator.py writes to disk:
#   single week  →  generated_week.md  /  generated_week.json
#   3-month      →  generated_week_3month.md  /  generated_week_3month.json
if [[ "$THREE_MONTHS" == true ]]; then
  MD_OUT="generated_week_3month.md"
  JSON_OUT="generated_week_3month.json"
else
  MD_OUT="generated_week.md"
  JSON_OUT="generated_week.json"
fi

# ── Print settings banner ─────────────────────────────────────
echo
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [[ "$THREE_MONTHS" == true ]]; then
  echo -e "${BOLD}  Generating ${WEEKS}-week Training Block${NC}"
else
  echo -e "${BOLD}  Generating Weekly Workout${NC}"
fi
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Settings${NC}"
echo -e "  Mode       : $( [[ "$THREE_MONTHS" == true ]] \
    && echo "${GREEN}3-month block (${WEEKS} weeks)${NC}" \
    || echo "Single week" )"
echo -e "  Progression: $( [[ -n "$INC" ]] \
    && echo "${GREEN}+${INC} lb/wk override (all exercises)${NC}" \
    || echo "${YELLOW}Built-in rules (+5 compound / +2.5 accessory / 0 bodyweight)${NC}" )"
echo -e "  Running    : $( [[ "$ADD_RUN" == true ]] \
    && echo "${GREEN}Yes (incl. FARTLEK variants)${NC}" \
    || echo "No" )"
echo -e "  Days/week  : ${DAYS}"
echo

# ── Archive previous output ───────────────────────────────────
mkdir -p progress

if [[ "$THREE_MONTHS" == true ]]; then
  if [[ -f "generated_week_3month.json" ]]; then
    bak="progress/block_$(date +%Y%m%d_%H%M%S).json"
    cp generated_week_3month.json "$bak"
    echo -e "${GREEN}✓ Previous block archived → ${bak}${NC}"
  fi
  # Stale single-week files go to progress/ too
  if [[ -f "generated_week.json" ]]; then
    cp generated_week.json "progress/week_$(date +%Y%m%d_%H%M%S).json" 2>/dev/null || true
    echo -e "${GREEN}✓ Stale single-week file moved to progress/${NC}"
  fi
else
  # Single-week rollover: current → previous_week.json (fatigue baseline)
  if [[ -f "generated_week.json" ]]; then
    bak="progress/week_$(date +%Y%m%d_%H%M%S).json"
    cp generated_week.json "$bak"
    mv generated_week.json previous_week.json
    echo -e "${GREEN}✓ Previous week archived → ${bak}${NC}"
    echo -e "${GREEN}✓ previous_week.json updated (fatigue baseline for this week)${NC}"
  fi
fi

# ── Clean stale outputs ───────────────────────────────────────
echo -e "${BLUE}Cleaning old output files…${NC}"
rm -f generated_week.md generated_week_3month.md
rm -f workout_*.pdf workout_3month_*.pdf

# ── Run the generator ─────────────────────────────────────────
echo -e "${BLUE}Running:${NC} ${CYAN}python3 workout_generator.py ${PYARGS[*]}${NC}"
echo
python3 workout_generator.py "${PYARGS[@]}"

# ── Summary ───────────────────────────────────────────────────
echo
echo -e "${GREEN}${BOLD}✓ Complete!${NC}"
echo
echo -e "${BOLD}Files written:${NC}"
[[ -f "$MD_OUT"            ]] && echo -e "  ${GREEN}${MD_OUT}${NC}"
[[ -f "$JSON_OUT"          ]] && echo -e "  ${GREEN}${JSON_OUT}${NC}"
[[ -f "previous_week.json" ]] && echo -e "  ${GREEN}previous_week.json${NC}"
if [[ "$THREE_MONTHS" == true ]]; then
  echo -e "  ${GREEN}_posts/YYYY-MM-DD-workout.md${NC}  × ${WEEKS}  (one Jekyll post per week)"
fi

echo
echo -e "${BOLD}Next steps:${NC}"
if [[ "$THREE_MONTHS" == true ]]; then
  echo -e "  Next 3-month block : ${CYAN}bash nextWeek.sh -3${NC}"
  [[ "$PDF" == false ]] && \
  echo -e "  Export to PDF      : ${CYAN}bash nextWeek.sh -3 --pdf${NC}"
else
  echo -e "  Next week          : ${CYAN}bash nextWeek.sh${NC}"
  echo -e "  Run a full block   : ${CYAN}bash nextWeek.sh -3${NC}"
fi
echo