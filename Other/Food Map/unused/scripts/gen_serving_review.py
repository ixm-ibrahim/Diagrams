"""Generate a serving-audit review dump for a slice of one meal file.

Usage:
    python scripts/gen_serving_review.py <file> <start> <count> > out.txt

<file> is one of: curated | compositional | corpus
Dumps each meal with id, name, cuisine, categories, and the system's
computed serving_grams / plate_grams / per-100g cals / per-serving
cals+carbs+protein+fat — plus blank EST_* columns for the auditor's
independent estimate. Ordered by descending frequency (matches the
batch-by-frequency convention of the content audit).
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path

# Meal names carry CJK / Vietnamese / accented chars; force UTF-8 stdout so
# `> out.txt` redirection doesn't die on the Windows cp1252 default.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent))
from serving_audit_lib import Auditor, DATA

FILES = {
    'curated': 'meals.json',
    'compositional': 'compositional-meals.json',
    'corpus': 'corpus-titled-meals.json',
}


def main():
    which = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    meals = json.load((DATA / FILES[which]).open(encoding='utf-8'))
    meals = sorted(meals, key=lambda m: -(m.get('frequency') or 0))
    a = Auditor()
    sl = meals[start:start + count]
    print(f'# serving-audit review — {which} [{start}:{start+count}] of {len(meals)}')
    print('# columns: idx | id | name | cuisine | serv_g | plate_g | cal100 | calSrv | carbSrv | protSrv | fatSrv')
    print('#   then your estimate: EST_serv_g | EST_calSrv | EST_cal100 | CLASS(none/serving/density/both/mystery) | SOURCE/NOTE')
    print('# cats listed on the following line for each meal.')
    print()
    for i, m in enumerate(sl, start=start):
        s = a.summary(m)
        print(f'[{i}] {m["id"]} | {m["name"]} | {m.get("cuisine") or "-"} | '
              f'serv={s["serving_grams"]} plate={s["plate_grams"]} | '
              f'cal100={s["cal_100g"]} calSrv={s["cal_serving"]} '
              f'carbSrv={s["carb_serving"]} protSrv={s["protein_serving"]} fatSrv={s["fat_serving"]}')
        print(f'      cats: {m.get("ingredient_categories")}')
    print()
    print(f'# end — {len(sl)} meals')


if __name__ == '__main__':
    main()
