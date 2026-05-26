"""Shared harness for the serving-size / per-serving-nutrient audit.

Replicates exactly what the running app computes for each meal, so the
audit can compare the system's numbers against an independent real-world
estimate. The math mirrors aggregateMeals() in src/core/aggregations.js:

  - Each meal's ingredient_categories resolve to category aggregates
    (per-100g nutrients = equal-weighted mean of member ingredients).
  - plate_grams = Σ category serving_grams (from SERVING_GRAMS_BY_CATEGORY).
  - per-100g nutrient = Σ(cat[n] × cat_serving / 100) / plate_grams × 100
    (the gram-weighted mean of category densities).
  - per-serving nutrient = per-100g × display_serving / 100, where
    display_serving = meal.serving_grams override if present, else plate_grams.

This module is import-only; batch scripts drive it.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'src' / 'data'

NUTRIENT_FIELDS = [
    'calories', 'carbs', 'protein', 'fiber', 'fat', 'sodium', 'sugar',
    'saturated_fat', 'iron',
]
SERVING_GRAMS_DEFAULT = 100


def load_ingredients():
    with (DATA / 'ingredients.json').open(encoding='utf-8') as f:
        return json.load(f)


def load_schema_servings():
    """Parse SERVING_GRAMS_BY_CATEGORY from schema.js (object-literal -> JSON)."""
    schema_text = (DATA / 'schema.js').read_text(encoding='utf-8')
    m = re.search(r'SERVING_GRAMS_BY_CATEGORY\s*=\s*(\{.*?\})\s*;', schema_text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    block = re.sub(r'/\*.*?\*/', '', block, flags=re.DOTALL)
    block = re.sub(r'//[^\n]*', '', block)
    block = re.sub(r"'([^']+)'", r'"\1"', block)
    block = re.sub(r',(\s*[}\]])', r'\1', block)
    return json.loads(block)


def aggregate_categories(ingredients):
    """One record per category; per-100g nutrients = mean of members."""
    by_cat = defaultdict(list)
    for ing in ingredients:
        c = ing.get('category')
        if c:
            by_cat[c].append(ing)
    out = {}
    for cat, members in by_cat.items():
        n = len(members)
        agg = {'name': cat}
        for field in NUTRIENT_FIELDS:
            agg[field] = sum((m.get(field) or 0) for m in members) / n if n else 0
        out[cat] = agg
    return out


class Auditor:
    """Bundles the category aggregates + serving map and computes meal numbers."""

    def __init__(self):
        self.cat_aggs = aggregate_categories(load_ingredients())
        self.cat_servings = load_schema_servings()

    def plate_grams(self, meal):
        cats = [c for c in (meal.get('ingredient_categories') or []) if c in self.cat_aggs]
        if not cats:
            return 0.0
        pg = sum(self.cat_servings.get(c, SERVING_GRAMS_DEFAULT) for c in cats)
        return pg if pg > 0 else len(cats) * SERVING_GRAMS_DEFAULT

    def per_100g(self, meal):
        """Returns {nutrient: per-100g value} or None when no categories resolve."""
        cats = [c for c in (meal.get('ingredient_categories') or []) if c in self.cat_aggs]
        if not cats:
            return None
        pg = self.plate_grams(meal)
        out = {}
        for field in NUTRIENT_FIELDS:
            total = 0.0
            for c in cats:
                sg = self.cat_servings.get(c, SERVING_GRAMS_DEFAULT)
                total += (self.cat_aggs[c].get(field) or 0) * (sg / 100.0)
            out[field] = total / pg * 100.0
        return out

    def display_serving(self, meal):
        sg = meal.get('serving_grams')
        if isinstance(sg, (int, float)) and sg > 0:
            return float(sg)
        return self.plate_grams(meal)

    def per_serving(self, meal):
        """Returns {nutrient: per-serving value} or None."""
        p100 = self.per_100g(meal)
        if p100 is None:
            return None
        ds = self.display_serving(meal)
        return {k: v * ds / 100.0 for k, v in p100.items()}

    def summary(self, meal):
        """Compact dict of the numbers the audit cares about."""
        p100 = self.per_100g(meal)
        ds = self.display_serving(meal)
        pg = self.plate_grams(meal)
        ps = self.per_serving(meal)
        return {
            'plate_grams': round(pg, 1),
            'serving_grams': meal.get('serving_grams'),
            'display_serving': round(ds, 1),
            'cal_100g': round(p100['calories'], 1) if p100 else None,
            'cal_serving': round(ps['calories'], 1) if ps else None,
            'carb_serving': round(ps['carbs'], 1) if ps else None,
            'protein_serving': round(ps['protein'], 1) if ps else None,
            'fat_serving': round(ps['fat'], 1) if ps else None,
        }
