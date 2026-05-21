"""Phase 18: Beverages food_group expansion.

Adds ~85 new Beverages entries across all five categories:
  - Alcoholic beverages (~30)
  - Coffee & tea (~12)
  - Soft drinks (~10)
  - Juices (~10)
  - Prepared soups & broths (~15)

Tag rules:
  - `alcohol` on every alcoholic entry.
  - `caffeine` on coffee/espresso/black-or-green tea/cola/energy/matcha/chai/mocha.
  - `dairy` on cream-based / milk-based entries (latte, cappuccino, mocha,
    baileys-style, eggnog, cream-of soups).
  - `eggs` on eggnog.
  - `meat` on animal-derived broths/soups.
  - `gluten` on beer (barley malt) and any wheat-based entry.

Single-group rule:
  - plant [0,1,0] for plant-derived liquids (most entries).
  - dairy [0,0,1] for cream/milk-based (cream-of soups, eggnog, baileys, latte).
  - animal [1,0,0] for meat-derived broths and chicken noodle / French onion.

Idempotent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

FG = "Beverages"


def B(id, name, cat, sub, contains, gw, kcal, c, p, fb, fat, na, sg, sf, notes,
      form=None, examples=None):
    entry = {
        "id": id, "name": name, "category": cat, "subcategory": sub,
        "food_group": FG, "contains": list(contains), "group_weights": list(gw),
        "examples": list(examples) if examples else [],
        "calories": kcal, "carbs": c, "protein": p, "fiber": fb,
        "fat": fat, "sodium": na, "sugar": sg, "saturated_fat": sf,
        "notes": notes,
    }
    if form:
        entry["form"] = form
    return entry


PLANT = [0, 1, 0]
ANIMAL = [1, 0, 0]
DAIRY = [0, 0, 1]


# ---------------------------------------------------------------------------
# Alcoholic beverages (~30)
# ---------------------------------------------------------------------------
ALC_CAT = "Alcoholic beverages"

ALCOHOLS = [
    # Wine (8)
    B("wine-white", "White wine", ALC_CAT, "Wine", ["alcohol"], PLANT,
      82, 2.6, 0.1, 0, 0, 5, 1.0, 0, "Standard dry white, ~12% ABV.",
      examples=["chardonnay", "sauvignon blanc", "cooking liquid"]),
    B("wine-rose", "Rosé wine", ALC_CAT, "Wine", ["alcohol"], PLANT,
      83, 2.9, 0.1, 0, 0, 4, 1.4, 0, "Pink wine, ~11-12% ABV.",
      examples=["summer drink", "lighter pairing"]),
    B("wine-sparkling", "Sparkling wine / prosecco", ALC_CAT, "Wine", ["alcohol"], PLANT,
      84, 2.7, 0.2, 0, 0, 6, 1.4, 0, "Italian sparkling. Champagne = French equivalent."),
    B("wine-champagne", "Champagne", ALC_CAT, "Wine", ["alcohol"], PLANT,
      89, 1.6, 0.2, 0, 0, 6, 0.5, 0, "French sparkling wine, dry-style brut."),
    B("port-wine", "Port wine", ALC_CAT, "Wine", ["alcohol"], PLANT,
      157, 12, 0.1, 0, 0, 9, 12, 0, "Fortified sweet Portuguese wine, ~20% ABV."),
    B("sherry-dry", "Sherry (dry)", ALC_CAT, "Wine", ["alcohol"], PLANT,
      116, 1.4, 0.2, 0, 0, 9, 1.4, 0, "Fortified Spanish wine, ~15-17% ABV."),
    B("vermouth-dry", "Vermouth (dry)", ALC_CAT, "Wine", ["alcohol"], PLANT,
      105, 1.5, 0.1, 0, 0, 9, 1, 0, "Aromatized wine; martini base."),
    B("vermouth-sweet", "Vermouth (sweet)", ALC_CAT, "Wine", ["alcohol"], PLANT,
      158, 16, 0.1, 0, 0, 9, 14, 0, "Sweet aromatized wine; Manhattan/Negroni base."),
    B("marsala-wine", "Marsala wine (cooking)", ALC_CAT, "Wine", ["alcohol"], PLANT,
      121, 10, 0.1, 0, 0, 35, 7, 0, "Sicilian fortified wine; chicken/veal marsala."),

    # Beer (5)
    B("ale", "Ale", ALC_CAT, "Beer", ["alcohol", "gluten"], PLANT,
      52, 4.6, 0.5, 0, 0, 6, 0, 0, "Top-fermented beer, ~5% ABV."),
    B("ipa", "IPA (India Pale Ale)", ALC_CAT, "Beer", ["alcohol", "gluten"], PLANT,
      66, 5.5, 0.7, 0, 0, 5, 0.5, 0, "Hop-forward ale, ~6-7% ABV."),
    B("stout-beer", "Stout", ALC_CAT, "Beer", ["alcohol", "gluten"], PLANT,
      52, 4.3, 0.4, 0, 0, 8, 0, 0, "Dark roasted beer (Guinness-style), ~4-5% ABV."),
    B("wheat-beer", "Wheat beer", ALC_CAT, "Beer", ["alcohol", "gluten"], PLANT,
      45, 3.7, 0.5, 0, 0, 4, 0.3, 0, "Hefeweizen / witbier style."),
    B("hard-cider", "Hard cider", ALC_CAT, "Cider", ["alcohol"], PLANT,
      47, 4.5, 0.1, 0, 0, 4, 2.6, 0, "Fermented apple juice, ~5% ABV."),

    # Spirits (8)
    B("bourbon", "Bourbon whiskey", ALC_CAT, "Whisky", ["alcohol"], PLANT,
      250, 0, 0, 0, 0, 1, 0, 0, "American corn whiskey, 80-proof."),
    B("scotch-whisky", "Scotch whisky", ALC_CAT, "Whisky", ["alcohol"], PLANT,
      250, 0, 0, 0, 0, 1, 0, 0, "Malt or blended; 80-100 proof."),
    B("rye-whiskey", "Rye whiskey", ALC_CAT, "Whisky", ["alcohol", "gluten"], PLANT,
      250, 0, 0, 0, 0, 1, 0, 0, "Rye-grain American whiskey; Manhattan classic."),
    B("gin", "Gin", ALC_CAT, "Gin", ["alcohol"], PLANT,
      263, 0, 0, 0, 0, 1, 0, 0, "Juniper-flavored, 80-94 proof."),
    B("rum-light", "Rum (white)", ALC_CAT, "Rum", ["alcohol"], PLANT,
      231, 0, 0, 0, 0, 1, 0, 0, "Clear rum, 80-proof. Daiquiri/mojito base."),
    B("rum-dark", "Rum (dark)", ALC_CAT, "Rum", ["alcohol"], PLANT,
      249, 0.6, 0, 0, 0, 1, 0.5, 0, "Aged molasses rum, deeper flavor."),
    B("tequila", "Tequila", ALC_CAT, "Tequila", ["alcohol"], PLANT,
      231, 0, 0, 0, 0, 1, 0, 0, "Blue agave spirit, 80-proof."),
    B("brandy", "Brandy / cognac", ALC_CAT, "Brandy", ["alcohol"], PLANT,
      231, 0, 0, 0, 0, 1, 0, 0, "Distilled wine, 80-proof."),

    # Liqueurs (8)
    B("amaretto", "Amaretto", ALC_CAT, "Liqueurs", ["alcohol"], PLANT,
      280, 30, 0, 0, 0, 1, 28, 0, "Almond-flavored sweet liqueur."),
    B("kahlua", "Coffee liqueur (Kahlua-style)", ALC_CAT, "Liqueurs", ["alcohol", "caffeine"], PLANT,
      336, 47, 0.1, 0, 0, 5, 46, 0, "Sweet coffee liqueur, espresso martini base."),
    B("baileys-style", "Cream liqueur (Baileys-style)", ALC_CAT, "Liqueurs", ["alcohol", "dairy"], DAIRY,
      327, 25, 3, 0, 13, 50, 20, 8, "Irish cream liqueur; whiskey + dairy cream."),
    B("triple-sec", "Triple sec / Cointreau", ALC_CAT, "Liqueurs", ["alcohol"], PLANT,
      255, 25, 0, 0, 0, 1, 24, 0, "Orange-peel liqueur. Margarita/sidecar base."),
    B("sambuca", "Sambuca", ALC_CAT, "Liqueurs", ["alcohol"], PLANT,
      350, 41, 0, 0, 0, 1, 40, 0, "Italian anise liqueur."),
    B("schnapps-peppermint", "Peppermint schnapps", ALC_CAT, "Liqueurs", ["alcohol"], PLANT,
      298, 30, 0, 0, 0, 1, 28, 0, "Sweet mint liqueur."),
    B("absinthe", "Absinthe", ALC_CAT, "Liqueurs", ["alcohol"], PLANT,
      348, 0, 0, 0, 0, 1, 0, 0, "Anise + wormwood; 110-140 proof."),
    B("sake", "Sake", ALC_CAT, "Wine", ["alcohol"], PLANT,
      134, 5, 0.5, 0, 0, 2, 0, 0, "Japanese rice wine, ~15-16% ABV."),
]


# ---------------------------------------------------------------------------
# Coffee & tea (~12)
# ---------------------------------------------------------------------------
CT_CAT = "Coffee & tea"

COFFEE_TEA = [
    B("espresso", "Espresso", CT_CAT, "Coffee", ["caffeine"], PLANT,
      9, 1.7, 0.1, 0, 0.2, 14, 0, 0, "Concentrated brewed coffee; ~30-50ml shot.",
      examples=["macchiato base", "espresso martini", "ristretto"]),
    B("instant-coffee", "Instant coffee (prepared)", CT_CAT, "Coffee", ["caffeine"], PLANT,
      2, 0.3, 0.1, 0, 0, 2, 0, 0, "Freeze-dried granules dissolved in water."),
    B("cold-brew-coffee", "Cold brew coffee", CT_CAT, "Coffee", ["caffeine"], PLANT,
      2, 0, 0.1, 0, 0, 4, 0, 0, "Slow-steeped coffee, low acidity."),
    B("decaf-coffee", "Decaf coffee (brewed)", CT_CAT, "Coffee", [], PLANT,
      1, 0, 0.1, 0, 0, 2, 0, 0, "Brewed coffee with caffeine removed (>97%)."),
    B("latte", "Latte", CT_CAT, "Coffee", ["caffeine", "dairy"], DAIRY,
      56, 4.7, 3, 0, 2.5, 38, 4.6, 1.5, "Espresso + steamed milk.",
      examples=["coffeeshop staple", "morning drink"]),
    B("cappuccino", "Cappuccino", CT_CAT, "Coffee", ["caffeine", "dairy"], DAIRY,
      45, 3.5, 2.5, 0, 2, 30, 3.5, 1.3, "Espresso + steamed + foamed milk."),
    B("mocha-coffee", "Mocha", CT_CAT, "Coffee", ["caffeine", "dairy"], DAIRY,
      87, 12, 2.5, 0.5, 3, 50, 10, 1.8, "Espresso + chocolate + steamed milk."),
    B("green-tea", "Green tea (brewed)", CT_CAT, "Tea", ["caffeine"], PLANT,
      1, 0.2, 0.2, 0, 0, 1, 0, 0, "Unoxidized leaf tea. ~15-30mg caffeine/100g."),
    B("white-tea", "White tea (brewed)", CT_CAT, "Tea", ["caffeine"], PLANT,
      1, 0.2, 0, 0, 0, 1, 0, 0, "Minimally processed tea leaves. Light caffeine."),
    B("oolong-tea", "Oolong tea (brewed)", CT_CAT, "Tea", ["caffeine"], PLANT,
      1, 0.2, 0, 0, 0, 3, 0, 0, "Partially oxidized tea; caffeine between green/black."),
    B("herbal-tea", "Herbal tea (brewed)", CT_CAT, "Tea", [], PLANT,
      1, 0.2, 0, 0, 0, 2, 0, 0, "Tisane (chamomile, rooibos, etc.); caffeine-free."),
    B("matcha", "Matcha (powder, prepared)", CT_CAT, "Tea", ["caffeine"], PLANT,
      4, 1.0, 0.3, 0.3, 0, 1, 0, 0, "Stone-ground green tea, whisked in water.",
      form="powdered"),
    B("chai-concentrate", "Chai concentrate", CT_CAT, "Tea", ["caffeine"], PLANT,
      57, 13, 0.4, 0, 0.1, 35, 12, 0, "Spiced black tea concentrate; mix 1:1 with milk."),
]


# ---------------------------------------------------------------------------
# Soft drinks (~10)
# ---------------------------------------------------------------------------
SD_CAT = "Soft drinks"

SODAS = [
    B("diet-cola", "Diet cola", SD_CAT, "Soft drinks", ["caffeine"], PLANT,
      0, 0, 0, 0, 0, 12, 0, 0, "Sugar-free cola with aspartame/sucralose; same caffeine."),
    B("lemon-lime-soda", "Lemon-lime soda", SD_CAT, "Soft drinks", [], PLANT,
      41, 10.4, 0, 0, 0, 12, 10.4, 0, "Sprite/7-Up style. Caffeine-free."),
    B("root-beer", "Root beer", SD_CAT, "Soft drinks", [], PLANT,
      41, 10.6, 0, 0, 0, 13, 10.6, 0, "Sassafras/wintergreen-flavored. Caffeine-free."),
    B("club-soda", "Club soda", SD_CAT, "Soft drinks", [], PLANT,
      0, 0, 0, 0, 0, 21, 0, 0, "Carbonated water with added minerals."),
    B("tonic-water", "Tonic water", SD_CAT, "Soft drinks", [], PLANT,
      34, 8.8, 0, 0, 0, 4, 8.8, 0, "Quinine-flavored. Gin-and-tonic base."),
    B("sparkling-water", "Sparkling water", SD_CAT, "Soft drinks", [], PLANT,
      0, 0, 0, 0, 0, 2, 0, 0, "Plain carbonated water (La Croix, Perrier)."),
    B("energy-drink", "Energy drink (Red Bull-style)", SD_CAT, "Soft drinks", ["caffeine"], PLANT,
      45, 11, 0.4, 0, 0, 41, 11, 0, "Caffeinated sugary drink; ~32mg caffeine/100g."),
    B("sports-drink", "Sports drink (Gatorade-style)", SD_CAT, "Soft drinks", [], PLANT,
      25, 6.0, 0, 0, 0, 41, 5.9, 0, "Electrolyte + sugar; rehydration drink."),
    B("iced-tea-sweetened", "Iced tea (bottled, sweetened)", SD_CAT, "Soft drinks", ["caffeine"], PLANT,
      32, 7.9, 0, 0, 0, 9, 7.9, 0, "Sweetened black tea, bottled."),
    B("eggnog", "Eggnog", SD_CAT, "Dairy beverages", ["dairy", "eggs"], DAIRY,
      135, 14, 4, 0, 6.9, 54, 14, 4.2, "Milk + cream + egg yolk + sugar + nutmeg."),
]


# ---------------------------------------------------------------------------
# Juices (~10)
# ---------------------------------------------------------------------------
JC_CAT = "Juices"

JUICES = [
    B("grape-juice", "Grape juice", JC_CAT, "Fruit juices", [], PLANT,
      60, 14.8, 0.4, 0.2, 0.1, 5, 14.2, 0, "Concord-style purple grape juice."),
    B("cranberry-juice", "Cranberry juice (cocktail)", JC_CAT, "Fruit juices", [], PLANT,
      46, 12, 0, 0, 0, 2, 12, 0, "Sweetened juice cocktail; pure cranberry is much tarter."),
    B("pineapple-juice", "Pineapple juice", JC_CAT, "Fruit juices", [], PLANT,
      53, 12.9, 0.4, 0.2, 0.1, 2, 9.9, 0, "Unsweetened canned."),
    B("grapefruit-juice", "Grapefruit juice", JC_CAT, "Fruit juices", [], PLANT,
      39, 9.2, 0.5, 0.1, 0.1, 1, 8.5, 0, "Pink or white, unsweetened."),
    B("tomato-juice", "Tomato juice", JC_CAT, "Vegetable juices", [], PLANT,
      17, 4.1, 0.8, 0.4, 0.1, 253, 2.6, 0, "Canned, salted. Bloody Mary base."),
    B("vegetable-juice", "Vegetable juice (V8-style)", JC_CAT, "Vegetable juices", [], PLANT,
      22, 5.0, 0.7, 0.7, 0.1, 220, 3.5, 0, "Tomato-based vegetable blend juice."),
    B("lemonade", "Lemonade", JC_CAT, "Fruit juices", [], PLANT,
      40, 10.4, 0.1, 0, 0.05, 4, 9.8, 0, "Sweetened lemon juice + water."),
    B("pomegranate-juice", "Pomegranate juice", JC_CAT, "Fruit juices", [], PLANT,
      54, 13.1, 0.2, 0.1, 0.3, 9, 12.7, 0, "Tart antioxidant-rich juice."),
    B("prune-juice", "Prune juice", JC_CAT, "Fruit juices", [], PLANT,
      71, 17.4, 0.6, 1.0, 0.03, 4, 16.5, 0, "Strained stewed prunes."),
    B("coconut-water", "Coconut water", JC_CAT, "Fruit juices", [], PLANT,
      19, 3.7, 0.7, 1.1, 0.2, 105, 2.6, 0.2, "Liquid from young green coconuts."),
    B("fruit-nectar", "Fruit nectar", JC_CAT, "Fruit nectars", [], PLANT,
      54, 13.4, 0.4, 0.2, 0.05, 7, 13, 0, "Pureed fruit + sugar + water (peach, pear, mango)."),
]


# ---------------------------------------------------------------------------
# Prepared soups & broths (~15)
# ---------------------------------------------------------------------------
PS_CAT = "Prepared soups & broths"

SOUPS = [
    B("vegetable-broth", "Vegetable broth (canned)", PS_CAT, "Broths & stocks", [], PLANT,
      12, 2, 0.5, 0, 0.2, 359, 1, 0, "Carrot/celery/onion-derived broth.", form="canned"),
    B("bone-broth-chicken", "Bone broth (chicken)", PS_CAT, "Broths & stocks", ["meat"], ANIMAL,
      36, 1, 9, 0, 0.4, 220, 0.5, 0.1, "Long-simmered bone broth, high protein.", form="canned"),
    B("mushroom-broth", "Mushroom broth", PS_CAT, "Broths & stocks", [], PLANT,
      11, 2, 0.5, 0.1, 0, 350, 0.8, 0, "Concentrated mushroom-stock liquid.", form="canned"),
    B("dashi", "Dashi", PS_CAT, "Broths & stocks", ["fish"], ANIMAL,
      4, 0.5, 0.5, 0, 0, 250, 0.2, 0, "Japanese kombu + bonito stock.", form="cooked"),
    B("miso-broth", "Miso broth", PS_CAT, "Broths & stocks", ["soy"], PLANT,
      36, 5, 2, 0.5, 1, 1100, 1.5, 0.2, "Miso paste dissolved in water/dashi."),
    B("bouillon-cube-chicken", "Bouillon cube (chicken)", PS_CAT, "Broths & stocks", ["meat"], ANIMAL,
      219, 18, 13, 0.7, 9, 23875, 0.5, 4, "Dehydrated stock concentrate; very salty.",
      form="paste"),
    B("bouillon-cube-beef", "Bouillon cube (beef)", PS_CAT, "Broths & stocks", ["meat"], ANIMAL,
      219, 18, 13, 0.7, 9, 23875, 0.5, 4, "Dehydrated beef-stock concentrate.", form="paste"),
    B("bouillon-cube-vegetable", "Bouillon cube (vegetable)", PS_CAT, "Broths & stocks", [], PLANT,
      209, 22, 8, 1, 9, 24000, 0.5, 1.5, "Vegan dehydrated stock concentrate.", form="paste"),

    B("cream-of-chicken-soup", "Cream of chicken soup (condensed)", PS_CAT, "Broths & stocks",
      ["meat", "dairy", "gluten"], DAIRY,
      88, 7, 2.7, 0.2, 5.5, 678, 0.5, 1.6, "Canned condensed; per-100g undiluted.", form="canned"),
    B("cream-of-celery-soup", "Cream of celery soup (condensed)", PS_CAT, "Broths & stocks",
      ["dairy", "gluten"], DAIRY,
      72, 7, 1.3, 0.6, 4.6, 691, 1, 1.2, "Canned condensed.", form="canned"),
    B("tomato-soup", "Tomato soup (canned)", PS_CAT, "Broths & stocks", ["dairy"], PLANT,
      31, 6.7, 0.8, 0.7, 0.5, 471, 4.4, 0.1, "Canned, prepared with water.", form="canned"),
    B("chicken-noodle-soup", "Chicken noodle soup (canned)", PS_CAT, "Broths & stocks",
      ["meat", "gluten"], ANIMAL,
      24, 3, 1.3, 0.2, 0.7, 343, 0.4, 0.2, "Standard canned, prepared.", form="canned"),
    B("french-onion-soup", "French onion soup", PS_CAT, "Broths & stocks", ["meat", "gluten"], ANIMAL,
      57, 8, 1.6, 0.7, 1.9, 405, 4, 0.7, "Beef-broth-based onion soup."),
    B("minestrone", "Minestrone", PS_CAT, "Broths & stocks", ["gluten"], PLANT,
      34, 5.7, 1.7, 1.0, 0.6, 326, 1.4, 0.1, "Italian bean + vegetable + pasta soup."),
    B("lentil-soup", "Lentil soup", PS_CAT, "Broths & stocks", [], PLANT,
      57, 10, 4, 1.7, 0.8, 326, 1.3, 0.1, "Brown/red lentil + vegetable soup."),
    B("butternut-squash-soup", "Butternut squash soup", PS_CAT, "Broths & stocks", ["dairy"], DAIRY,
      59, 9, 1.5, 1.3, 2.2, 410, 4, 1.3, "Pureed roasted-squash soup with cream."),
]


ALL_NEW = ALCOHOLS + COFFEE_TEA + SODAS + JUICES + SOUPS


def main() -> None:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    by_id = {ing["id"]: ing for ing in data}

    appended = 0
    skipped = 0
    for entry in ALL_NEW:
        if entry["id"] in by_id:
            print(f"  ! skipped — id {entry['id']} already exists", file=sys.stderr)
            skipped += 1
            continue
        gw = entry["group_weights"]
        assert len(gw) == 3 and sum(gw) == 1 and gw.count(1) == 1 and gw.count(0) == 2, \
            f"{entry['id']} violates single-group rule: {gw}"
        assert entry["food_group"] == "Beverages", f"{entry['id']} has food_group={entry['food_group']}"
        data.append(entry)
        appended += 1

    print(f"\nSummary: {appended} new entries appended, {skipped} skipped.")
    write_compact(data, ING_PATH)
    print(f"Wrote {len(data)} entries to {ING_PATH}.")


def write_compact(data, path: Path) -> None:
    lines = ["["]
    for i, ing in enumerate(data):
        sep = "," if i < len(data) - 1 else ""
        lines.append("  " + json.dumps(ing, ensure_ascii=False, separators=(", ", ": ")) + sep)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
