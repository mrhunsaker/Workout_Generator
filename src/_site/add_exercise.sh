#!/usr/bin/env bash
#
# add_exercise.sh
# Helper to add new exercises to exercise_library.json
# Fully aligned with current schema (roles, muscle_groups, exclusion)

FILE="exercise_library.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: 'jq' is required but not installed."
  exit 1
fi

echo "--- Add New Exercise to Library ---"
echo "Leave optional fields blank if not applicable."
echo

read -p "Exercise Name (e.g. Goblet Front Squat): " NAME
read -p "Exercise ID (e.g. goblet_front_squat): " ID

read -p "Body Regions (comma separated, e.g. lower,core): " REGIONS
read -p "Muscle Groups (comma separated, e.g. quadriceps,gluteus_maximus): " MUSCLES

read -p "Movement Pattern (e.g. squat, hinge, horizontal_push): " PATTERN
read -p "Plane of Motion (sagittal, frontal, transverse, multi): " PLANE

read -p "Roles (comma separated, e.g. primary_lower,integration): " ROLES
read -p "Equipment (comma separated, e.g. dumbbell,kettlebell | leave blank for bodyweight): " EQUIP

read -p "Ladder Eligible? (true/false): " LADDER
read -p "Position (ground/standing): " POS
read -p "Exclusion IDs (comma separated exercise IDs, e.g. jump_squat,box_squat | optional): " EXCLUDE

# Convert comma‑separated strings to JSON arrays
to_json_array() {
  local input="$1"
  if [[ -z "$input" ]]; then
    echo "[]"
  else
    echo "\"$input\"" | jq -R -s -c .
  fi
}

# Build the JSON snippet for the new exercise
NEW_EXERCISE=$(jq -n \
  --arg name "$NAME" \
  --arg id "$ID" \
  --argjson regions "$(to_json_array "$REGIONS")" \
  --argjson muscles "$(to_json_array "$MUSCLES")" \
  --arg pattern "$PATTERN" \
  --arg plane "$PLANE" \
  --arg json roles "$(to_json_array "$ROLES")" \
  --arg json equip "$(to_json_array "$EQUIP")" \
  --arg ladder "$LADDER" \
  --arg pos "$POS" \
  --arg json exclude "$(to_json_array "$EXCLUDE")" \
  --arg json default_load "$default_load" \
  --arg units "$units" \
  --arg reptype "$reptype" \
  --arg reps "$reps" \
  '
    {
      "id": $id,
      "name": $name,
      "body_regions": $regions,
      "muscle_groups": $muscles,
      "movement_pattern": $pattern,
      "plane_of_motion": $plane,
      "roles": $roles,
      "equipment": $equip,
      "ladder_eligible": $ladder,
      "ground_or_standing": $pos,
      "exclusion": $exclude,
      "default_load": $default_load,
      "units": $units,
      "reptype": $reptype,
      "reps": $reps
    }
  ')

# Read the existing library (or start with an empty array if file doesn't exist)
LIBRARY=$(jq -r '.[]' "$FILE" 2>/dev/null || echo "[]")

# Find the position to insert the new exercise (by ID)
INDEX=$(jq -r --arg id "$ID" '.[] | select(.id == $id) | length' <<<"$LIBRARY")

# Insert the new exercise
NEW_LIBRARY=$(jq -s --argjson exercise "$NEW_EXERCISE" '
  ($argjson.exercise | @json) + ($LIBRARY | add)
' "$LIBRARY")

# Write the updated library back to the file
jq -n --argfile lib "$NEW_LIBRARY" '. = $lib' "$FILE" > "$FILE.tmp" && mv "$FILE.tmp" "$FILE"

echo "Exercise added successfully."
echo "Updated library saved to $FILE"
