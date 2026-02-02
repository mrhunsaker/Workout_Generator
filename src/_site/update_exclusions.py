#!/usr/bin/env python3
import json
from collections import defaultdict

EXERCISE_FILE = "src/exercise_library.json"

KEYWORDS = [
    "lunge",
    "squat",
    "plank",
    "hamstring",
    "curl",
    "deadlift",
    "press",
    "row",
    "push",
    "pull",
    "calf",
    "bridge",
    "hinge",
    "step",
    "pistol",
    "split",
    "thruster",
    "extension",
    "rotation",
]

def extract_keywords(ex):
    """Return a set of family keywords for an exercise using movement_pattern, id and name."""
    ks = set()
    mp = ex.get('movement_pattern','') or ''
    # movement pattern heuristics: map patterns containing a keyword to that keyword
    for kw in KEYWORDS:
        if kw in mp:
            ks.add(kw)
    # check id and name
    eid = ex.get('id','').lower()
    name = ex.get('name','').lower()
    for kw in KEYWORDS:
        if kw in eid or kw in name:
            ks.add(kw)
    # fallback: if movement pattern ends with _squat or contains 'squat'
    if 'squat' in mp and 'squat' not in ks:
        ks.add('squat')
    return ks

def main():
    with open(EXERCISE_FILE, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    # Build mapping from keyword -> ids
    keyword_map = defaultdict(set)
    id_map = {ex['id']: ex for ex in exercises}
    for ex in exercises:
        ks = extract_keywords(ex)
        for k in ks:
            keyword_map[k].add(ex['id'])

    changed = 0
    diffs = {}
    for ex in exercises:
        eid = ex['id']
        ks = extract_keywords(ex)
        same_class_ids = set()
        for k in ks:
            same_class_ids.update(keyword_map.get(k, set()))
        same_class_ids.discard(eid)
        existing = [x for x in ex.get('exclusion', []) if x and x != 'none']
        new_excl_set = set(existing) | same_class_ids
        new_excl = sorted(new_excl_set)
        if new_excl != ex.get('exclusion', []):
            diffs[eid] = {
                'old': ex.get('exclusion', []),
                'new': new_excl,
            }
            ex['exclusion'] = new_excl
            changed += 1

    if changed:
        with open(EXERCISE_FILE, "w", encoding="utf-8") as f:
            json.dump(exercises, f, indent=2, ensure_ascii=False)
    print(f"Updated exclusions for {changed} exercises.")
    if changed:
        for eid, d in diffs.items():
            print(f"- {eid}: {len(d['old'])} -> {len(d['new'])} exclusions")

if __name__ == '__main__':
    main()
