"""Phase 17: Grains expansion.

Adds ~80 new Grains-food_group entries from MISSING_INGREDIENTS_CLEAN.csv,
covering Bread & baked goods (the largest new category), additional pasta
varieties, whole-grain extras, baking/stuffing/cereal mixes, and a few
specialty flours. All entries follow the schema: single-group plant
group_weights [0,1,0], USDA-style per-100g values, `gluten` in `contains`
where applicable (egg-based pasta also tags `eggs`).

Idempotent: re-running skips ids already present.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"


def G(id, name, cat, sub, fg, contains, kcal, c, p, fb, fat, na, sg, sf, notes,
      form=None, gw=None):
    """Compact constructor. fg defaults handled by caller per-section."""
    entry = {
        "id": id, "name": name, "category": cat, "subcategory": sub,
        "food_group": fg,
        "contains": list(contains),
        "group_weights": gw or [0, 1, 0],
        "examples": [],  # populated per-entry below where useful
        "calories": kcal, "carbs": c, "protein": p, "fiber": fb,
        "fat": fat, "sodium": na, "sugar": sg, "saturated_fat": sf,
        "notes": notes,
    }
    if form:
        entry["form"] = form
    return entry


# ---------------------------------------------------------------------------
# Bread & baked goods (Grains food_group)
# ---------------------------------------------------------------------------
BBG = "Bread & baked goods"

BAKED = [
    # --- Biscuits ---
    G("biscuit", "Biscuit (American)", BBG, "Biscuits", "Grains", ["gluten", "dairy"],
      353, 44, 7, 1.5, 16, 580, 5, 4, "Buttermilk biscuit; flaky baked good."),
    G("buttermilk-biscuit", "Buttermilk biscuit", BBG, "Biscuits", "Grains", ["gluten", "dairy"],
      356, 45, 7, 1.5, 16, 614, 5, 4, "Standard Southern-style biscuit, baked."),
    G("biscuit-mix", "Biscuit mix (Bisquick-style)", BBG, "Biscuits", "Grains", ["gluten", "dairy"],
      440, 70, 8, 2, 14, 1050, 8, 4, "Dry mix; milk/water added at use.", form="powdered"),
    G("digestive-biscuit", "Digestive biscuit", BBG, "Biscuits", "Grains", ["gluten"],
      471, 67, 7, 3.5, 19, 580, 18, 7, "UK whole-wheat sweet biscuit."),
    G("scone", "Scone", BBG, "Biscuits", "Grains", ["gluten", "dairy", "eggs"],
      396, 53, 8, 1.7, 18, 462, 14, 8, "British baked good with cream/butter."),

    # --- Bread ---
    G("multigrain-bread", "Multigrain bread", BBG, "Bread", "Grains", ["gluten"],
      265, 43, 13, 7, 4.2, 444, 6, 0.7, "Mixed-grain sandwich bread."),
    G("pumpernickel-bread", "Pumpernickel bread", BBG, "Bread", "Grains", ["gluten"],
      250, 47, 8.5, 6.5, 3.1, 596, 5, 0.4, "Dense German dark rye bread."),
    G("focaccia", "Focaccia", BBG, "Bread", "Grains", ["gluten"],
      291, 41, 8, 2.5, 11, 580, 1, 1.5, "Italian flat oven bread, olive-oil enriched."),
    G("challah", "Challah", BBG, "Bread", "Grains", ["gluten", "eggs"],
      323, 56, 10, 2.5, 6.5, 392, 8, 1.5, "Braided Jewish egg bread."),
    G("french-bread", "French bread", BBG, "Bread", "Grains", ["gluten"],
      272, 51, 9, 2.3, 3.0, 602, 2.5, 0.6, "Lean, crusty white loaf."),
    G("potato-bread", "Potato bread", BBG, "Bread", "Grains", ["gluten"],
      266, 49, 8, 2.0, 3.5, 389, 5, 0.8, "Soft sandwich loaf with potato in dough."),
    G("hawaiian-roll", "Hawaiian sweet roll", BBG, "Bread", "Grains", ["gluten", "eggs", "dairy"],
      342, 57, 9, 1.8, 8.5, 332, 14, 3, "Sweet pineapple-juice dinner roll."),
    G("hoagie-roll", "Hoagie roll", BBG, "Bread", "Grains", ["gluten"],
      280, 54, 9, 2.5, 3.0, 540, 4, 0.6, "Submarine / sub sandwich roll."),
    G("banana-bread", "Banana bread", BBG, "Bread", "Grains", ["gluten", "eggs"],
      326, 54, 4.3, 1.5, 11, 302, 30, 2.0, "Quick bread; sweet, dessert-leaning."),

    # --- Bread crumbs ---
    G("panko", "Panko (Japanese bread crumbs)", BBG, "Bread crumbs", "Grains", ["gluten"],
      370, 73, 12, 4, 2.5, 670, 4, 0.4, "Light, flaky Japanese-style crumb.", form="dried"),

    # --- Cookies ---
    G("chocolate-chip-cookie", "Chocolate chip cookie", BBG, "Cookies", "Grains", ["gluten", "dairy", "eggs", "caffeine"],
      488, 65, 5.5, 2.0, 24, 363, 36, 11, "Classic American baked cookie."),
    G("oatmeal-cookie", "Oatmeal cookie", BBG, "Cookies", "Grains", ["gluten", "dairy", "eggs"],
      450, 68, 6, 2.5, 18, 422, 32, 4.5, "Often raisin-studded."),
    G("sugar-cookie", "Sugar cookie", BBG, "Cookies", "Grains", ["gluten", "dairy", "eggs"],
      481, 68, 5, 0.9, 21, 374, 38, 9, "Simple butter-sugar cookie."),
    G("peanut-butter-cookie", "Peanut butter cookie", BBG, "Cookies", "Grains", ["gluten", "peanut", "dairy", "eggs"],
      483, 60, 8, 1.8, 24, 460, 33, 6, "Crisscross-pressed nut-butter cookie."),
    G("oreo", "Sandwich cookie (Oreo-style)", BBG, "Cookies", "Grains", ["gluten", "soy", "caffeine"],
      480, 71, 4.5, 2.4, 20, 460, 38, 5, "Chocolate sandwich with cream filling."),
    G("vanilla-wafer", "Vanilla wafer", BBG, "Cookies", "Grains", ["gluten", "dairy", "eggs"],
      438, 73, 5, 1.5, 14, 388, 33, 3.5, "Crispy round vanilla cookie."),
    G("ginger-snap", "Gingersnap", BBG, "Cookies", "Grains", ["gluten"],
      416, 76, 5.6, 2, 9.8, 661, 28, 2.4, "Crisp molasses + ginger cookie."),
    G("shortbread", "Shortbread", BBG, "Cookies", "Grains", ["gluten", "dairy"],
      502, 64, 6, 2, 24, 470, 18, 15, "Butter-rich crumbly cookie."),
    G("biscotti", "Biscotti", BBG, "Cookies", "Grains", ["gluten", "eggs", "tree_nut"],
      400, 67, 8, 2.5, 11, 264, 35, 2.2, "Twice-baked Italian cookie; often almond."),

    # --- Cornbread ---
    G("cornbread", "Cornbread", BBG, "Cornbread", "Grains", ["gluten", "dairy", "eggs"],
      305, 49, 7, 2.2, 9, 624, 11, 2.4, "Quick bread of cornmeal + wheat flour."),
    G("corn-muffin", "Corn muffin", BBG, "Cornbread", "Grains", ["gluten", "dairy", "eggs"],
      305, 51, 6, 1.6, 9, 595, 14, 2, "Sweet cornmeal muffin."),

    # --- Crackers ---
    G("soda-cracker", "Soda cracker", BBG, "Crackers", "Grains", ["gluten"],
      421, 73, 9, 2.7, 9, 1100, 1, 1.4, "Baking-soda-leavened plain cracker."),
    G("ritz-cracker", "Buttery round cracker (Ritz-style)", BBG, "Crackers", "Grains", ["gluten", "soy"],
      500, 63, 6.7, 2, 25, 800, 7, 4, "Round, butter-flavored cracker."),
    G("cheese-cracker", "Cheese cracker", BBG, "Crackers", "Grains", ["gluten", "dairy"],
      483, 60, 10, 2.5, 22, 1000, 5, 8, "Goldfish-/Cheez-It-style baked cracker."),
    G("water-cracker", "Water cracker", BBG, "Crackers", "Grains", ["gluten"],
      407, 74, 10, 2.5, 8, 720, 1, 1, "Plain crisp cracker for cheese boards."),
    G("rice-cracker", "Rice cracker", BBG, "Crackers", "Grains", ["soy"],
      398, 84, 7, 1.5, 2.5, 800, 1, 0.4, "Japanese senbei-style."),
    G("melba-toast", "Melba toast", BBG, "Crackers", "Grains", ["gluten"],
      388, 77, 12, 6.8, 3.2, 825, 3, 0.6, "Twice-baked thin dried bread toast."),
    G("pita-chip", "Pita chip", BBG, "Crackers", "Grains", ["gluten"],
      446, 68, 11, 4, 14, 633, 1, 2.0, "Baked seasoned pita pieces.", form="dried"),
    G("tortilla-chip", "Tortilla chip", BBG, "Crackers", "Grains", [],
      489, 65, 7, 4.7, 23, 460, 0.5, 3.3, "Fried/baked corn tortilla pieces."),
    G("doritos", "Flavored tortilla chip (Doritos-style)", BBG, "Crackers", "Grains", ["dairy"],
      498, 60, 7, 3.8, 26, 700, 2, 4, "Seasoned corn snack chip."),
    G("breadstick", "Breadstick (grissini)", BBG, "Crackers", "Grains", ["gluten"],
      412, 70, 12, 2.6, 9, 600, 1.4, 1.3, "Crisp Italian wand bread."),

    # --- Croutons ---
    G("croutons", "Croutons", BBG, "Croutons", "Grains", ["gluten"],
      407, 64, 10, 4, 12, 871, 4, 2.5, "Toasted seasoned bread cubes."),

    # --- Flatbread ---
    G("lavash", "Lavash", BBG, "Flatbread", "Grains", ["gluten"],
      282, 56, 9, 2.5, 1.6, 510, 1, 0.3, "Thin Armenian/Iranian unleavened bread."),
    G("matzo", "Matzo", BBG, "Flatbread", "Grains", ["gluten"],
      395, 84, 10, 3, 1.4, 1, 0.4, 0.2, "Unleavened Passover cracker-bread."),
    G("roti", "Roti", BBG, "Flatbread", "Grains", ["gluten"],
      297, 57, 10, 6, 4, 5, 2, 0.6, "Indian whole-wheat tortilla."),
    G("paratha", "Paratha", BBG, "Flatbread", "Grains", ["gluten"],
      361, 47, 7.5, 4.5, 16, 290, 1, 4, "Layered Indian griddle bread."),

    # --- Graham crackers ---
    G("graham-cracker-crumb", "Graham cracker crumbs", BBG, "Graham crackers", "Grains", ["gluten"],
      423, 79, 7, 2.7, 10, 580, 28, 1.7, "Crushed graham crackers for pie crusts."),

    # --- Muffins ---
    G("blueberry-muffin", "Blueberry muffin", BBG, "Muffins", "Grains", ["gluten", "eggs", "dairy"],
      377, 53, 6, 1.5, 16, 350, 28, 3, "Standard bakery muffin."),
    G("bran-muffin", "Bran muffin", BBG, "Muffins", "Grains", ["gluten", "eggs"],
      270, 47, 6, 5, 8, 380, 16, 1.5, "Fiber-forward breakfast muffin."),

    # --- Pastries ---
    G("danish", "Danish pastry", BBG, "Pastries", "Grains", ["gluten", "dairy", "eggs"],
      374, 41, 6.5, 1.3, 21, 350, 12, 7, "Laminated breakfast pastry."),
    G("puff-pastry", "Puff pastry", BBG, "Pastries", "Grains", ["gluten", "dairy"],
      558, 45, 7.3, 1.5, 38, 446, 0.3, 9.5, "Laminated dough, raw weight.", form="frozen"),
    G("phyllo-dough", "Phyllo dough", BBG, "Pastries", "Grains", ["gluten"],
      299, 53, 8, 2.0, 6, 482, 1, 1, "Paper-thin Greek pastry sheets.", form="frozen"),
    G("pie-crust", "Pie crust (baked)", BBG, "Pastries", "Grains", ["gluten"],
      506, 47, 6.2, 2, 33, 470, 0.4, 8.6, "Single-crust baked shell."),
    G("graham-cracker-crust", "Graham cracker crust", BBG, "Pastries", "Grains", ["gluten"],
      482, 60, 4, 1.5, 24, 470, 24, 5, "Pre-baked graham crumb crust."),

    # --- Pizza dough ---
    G("pizza-dough", "Pizza dough", BBG, "Pizza dough", "Grains", ["gluten"],
      265, 50, 9, 2.3, 3, 470, 2, 0.4, "Raw yeasted pizza base.", form="fresh"),

    # --- Pretzels ---
    G("hard-pretzel", "Hard pretzel", BBG, "Pretzels", "Grains", ["gluten"],
      384, 80, 10, 3, 3, 1240, 2.5, 0.6, "Crunchy baked snack pretzel."),
    G("soft-pretzel", "Soft pretzel", BBG, "Pretzels", "Grains", ["gluten"],
      338, 71, 8, 2, 3, 940, 1, 0.6, "Mall-style chewy pretzel."),

    # --- Rolls ---
    G("dinner-roll", "Dinner roll", BBG, "Rolls", "Grains", ["gluten", "dairy"],
      316, 54, 9, 2.4, 6, 540, 5, 1.6, "Soft yeasted side roll."),
    G("kaiser-roll", "Kaiser roll", BBG, "Rolls", "Grains", ["gluten"],
      301, 56, 10, 2.5, 4.3, 542, 2.4, 0.6, "Hard German-style sandwich roll."),
    G("burger-bun", "Hamburger bun", BBG, "Rolls", "Grains", ["gluten"],
      279, 50, 9, 2, 4.2, 478, 6, 1, "Soft round bun for burgers."),
    G("hot-dog-bun", "Hot dog bun", BBG, "Rolls", "Grains", ["gluten"],
      279, 50, 9, 2, 4.2, 478, 6, 1, "Soft elongated bun."),

    # --- Tortillas ---
    G("taco-shell", "Taco shell (hard)", BBG, "Tortillas", "Grains", [],
      484, 64, 7, 5.5, 23, 393, 0.7, 3.3, "Fried, folded corn tortilla."),

    # --- Wrappers ---
    G("wonton-wrapper", "Wonton wrapper", BBG, "Wrappers", "Grains", ["gluten", "eggs"],
      295, 59, 10, 2, 1.5, 580, 1, 0.3, "Thin square dough for wontons."),
    G("dumpling-wrapper", "Dumpling wrapper", BBG, "Wrappers", "Grains", ["gluten"],
      294, 60, 9, 2.2, 1.0, 380, 1, 0.2, "Round potsticker / gyoza skin."),
    G("spring-roll-wrapper", "Spring roll wrapper (rice)", BBG, "Wrappers", "Grains", [],
      330, 81, 0.9, 2, 0.4, 21, 0.5, 0.1, "Rice-flour translucent sheet."),
]


# ---------------------------------------------------------------------------
# Refined grains / Pasta
# ---------------------------------------------------------------------------
PASTA = [
    G("spaghetti", "Spaghetti (white)", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Dry semolina; standard long pasta.", form="dried"),
    G("fettuccine", "Fettuccine", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Flat ribbon pasta, dry.", form="dried"),
    G("linguine", "Linguine", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Flattened spaghetti, dry.", form="dried"),
    G("penne", "Penne", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Angled tube pasta.", form="dried"),
    G("rigatoni", "Rigatoni", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Large ridged tube pasta.", form="dried"),
    G("fusilli", "Fusilli", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Spiral pasta.", form="dried"),
    G("rotini", "Rotini", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Corkscrew pasta.", form="dried"),
    G("macaroni", "Macaroni", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Elbow pasta.", form="dried"),
    G("lasagna-noodle", "Lasagna noodle", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Wide flat sheets.", form="dried"),
    G("orzo", "Orzo", "Refined grains", "Pasta", "Grains", ["gluten"],
      371, 75, 13, 3.2, 1.5, 6, 2.7, 0.3, "Rice-shaped pasta.", form="dried"),
    G("egg-noodle", "Egg noodle", "Refined grains", "Pasta", "Grains", ["gluten", "eggs"],
      384, 71, 14, 3.3, 4.4, 21, 1.9, 1.1, "Wheat noodle with whole egg.", form="dried"),
    G("ravioli-cheese", "Ravioli (cheese, fresh)", "Refined grains", "Pasta", "Grains", ["gluten", "dairy", "eggs"],
      245, 31, 11, 2, 8.5, 380, 1.5, 4.0, "Fresh stuffed pasta.", form="fresh"),
    G("tortellini-cheese", "Tortellini (cheese, fresh)", "Refined grains", "Pasta", "Grains", ["gluten", "dairy", "eggs"],
      288, 36, 14, 2, 9, 600, 2, 4.5, "Ring-shaped stuffed pasta.", form="fresh"),
    G("ramen-noodle", "Ramen noodle (dried)", "Refined grains", "Noodles", "Grains", ["gluten"],
      436, 62, 10, 2, 17, 1731, 1, 8, "Instant fried wheat noodle (without seasoning).", form="dried"),
]


# ---------------------------------------------------------------------------
# Whole grains additions
# ---------------------------------------------------------------------------
WHOLE = [
    G("oatmeal-instant", "Oatmeal (instant, plain)", "Whole grains", "Oats", "Grains", [],
      368, 67, 13, 10, 7, 6, 1, 1.2, "Instant rolled oats; per dry 100g.", form="powdered"),
    G("granola", "Granola", "Whole grains", "Oats", "Grains", ["tree_nut"],
      471, 64, 11, 7, 20, 32, 21, 3.2, "Oats baked with sweeteners + nuts."),
    G("polenta", "Polenta (dry)", "Whole grains", "Wheat", "Grains", [],
      370, 79, 8, 7, 1.5, 1, 0.6, 0.2, "Coarse cornmeal; per dry 100g.", form="powdered"),
    G("grits", "Grits (dry)", "Whole grains", "Wheat", "Grains", [],
      371, 79, 8, 1.5, 1.2, 1, 0.4, 0.2, "Coarse white-corn porridge meal.", form="powdered"),
    G("wheat-germ", "Wheat germ", "Whole grains", "Whole grains", "Grains", ["gluten"],
      360, 52, 23, 13, 10, 12, 0, 1.7, "Nutrient-dense embryo of the wheat kernel."),
    G("hominy", "Hominy (canned)", "Whole grains", "Wheat", "Grains", [],
      72, 14, 1.5, 2.5, 0.9, 345, 0.4, 0.1, "Lye-treated corn kernels.", form="canned"),
    G("wheat-berries", "Wheat berries", "Whole grains", "Wheat", "Grains", ["gluten"],
      327, 71, 12, 12, 2, 2, 0.4, 0.5, "Whole unprocessed wheat kernels."),
]


# ---------------------------------------------------------------------------
# Prepared mixes (Grains-food_group subcategories)
# ---------------------------------------------------------------------------
PMIX = [
    G("baking-mix", "Baking mix (Bisquick-style)", "Prepared mixes", "Baking mixes", "Grains", ["gluten", "dairy"],
      440, 70, 8, 2, 14, 1050, 8, 4, "Dry mix for pancakes / biscuits.", form="powdered"),
    G("stuffing-mix", "Stuffing mix (dry)", "Prepared mixes", "Stuffing mixes", "Grains", ["gluten"],
      388, 75, 12, 3.5, 4.5, 1180, 5, 0.9, "Seasoned dry bread cubes.", form="dried"),
    G("granola-cereal", "Granola cereal", "Prepared mixes", "Cereals", "Grains", ["tree_nut"],
      450, 65, 11, 6.5, 18, 36, 18, 3, "Boxed granola cereal."),
    G("bran-cereal", "Bran cereal", "Prepared mixes", "Cereals", "Grains", ["gluten"],
      258, 80, 13, 29, 4.5, 700, 18, 0.6, "All-Bran-style high-fiber cereal."),
    G("corn-flakes", "Corn flakes", "Prepared mixes", "Cereals", "Grains", [],
      357, 84, 7.5, 3, 0.4, 729, 8, 0.1, "Toasted corn cereal flakes."),
    G("rice-cereal", "Rice cereal (crispy)", "Prepared mixes", "Cereals", "Grains", [],
      382, 87, 6, 1, 0.9, 793, 9, 0.2, "Rice Krispies-style cereal."),
]


# ---------------------------------------------------------------------------
# Flours
# ---------------------------------------------------------------------------
FLOURS = [
    G("rye-flour", "Rye flour", "Flours", "Wheat flours", "Grains", ["gluten"],
      349, 76, 11, 23, 1.5, 1, 1.6, 0.2, "Dark or medium rye; carries gluten.", form="powdered"),
    G("spelt-flour", "Spelt flour", "Flours", "Wheat flours", "Grains", ["gluten"],
      338, 70, 15, 11, 2.5, 8, 6.8, 0.4, "Whole-grain spelt; ancient wheat.", form="powdered"),
    G("vital-wheat-gluten", "Vital wheat gluten", "Flours", "Wheat flours", "Grains", ["gluten"],
      370, 14, 76, 0.6, 1.9, 29, 0, 0.3, "Concentrated wheat protein.", form="powdered"),
    G("arrowroot-starch", "Arrowroot starch", "Flours", "Starches", "Grains", [],
      357, 89, 0.3, 3.4, 0.1, 2, 0, 0, "Pure thickening starch; gluten-free.", form="powdered"),
]


ALL_NEW = BAKED + PASTA + WHOLE + PMIX + FLOURS


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
        # Single-group invariant
        gw = entry["group_weights"]
        assert len(gw) == 3 and sum(gw) == 1 and gw.count(1) == 1 and gw.count(0) == 2, \
            f"{entry['id']} violates single-group rule: {gw}"
        # food_group must be Grains for this phase
        assert entry["food_group"] == "Grains", f"{entry['id']} has food_group={entry['food_group']}"
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
