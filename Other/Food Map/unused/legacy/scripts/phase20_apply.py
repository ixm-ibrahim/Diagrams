"""Phase 20: Dairy + Processed cheese expansion.

Adds ~50 Dairy-food_group entries:
  - Processed cheese (~10)
  - Aged cheese additions (~10)
  - Fresh cheese additions (~6)
  - Frozen dairy (~8)
  - Fermented dairy / Milk extras (~10)
  - Plant milks (~3) — sorbet etc. (Note: sorbet is dairy-free; lives under
    Frozen dairy by structure but is plant-channel.)

All [0, 0, 1] dairy channel except plant-channel exceptions (sorbet, plant
milks already exist). Every entry carries `contains: ['dairy']` unless dairy-
free.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ING_PATH = ROOT / "src" / "data" / "ingredients.json"

FG = "Dairy"


def D(id, name, cat, sub, contains, gw, kcal, c, p, fb, fat, na, sg, sf, notes,
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
DAIRY = [0, 0, 1]


# ---------------------------------------------------------------------------
# Processed cheese (~10)
# ---------------------------------------------------------------------------
PC = "Processed cheese"

PROCESSED = [
    D("monterey-jack", "Monterey Jack", PC, "Semi-soft cheese", ["dairy"], DAIRY,
      373, 0.7, 24, 0, 30, 536, 0.5, 19, "Mild semi-soft American cow cheese."),
    D("pepper-jack", "Pepper Jack", PC, "Semi-soft cheese", ["dairy"], DAIRY,
      370, 0.7, 24, 0, 30, 580, 0.5, 18, "Monterey Jack with peppers + chilies."),
    D("colby", "Colby cheese", PC, "Semi-soft cheese", ["dairy"], DAIRY,
      394, 2.6, 24, 0, 32, 604, 0.5, 20, "Mild Wisconsin cow cheese; cheddar-adjacent."),
    D("colby-jack", "Colby-Jack", PC, "Semi-soft cheese", ["dairy"], DAIRY,
      384, 1.6, 24, 0, 31, 568, 0.5, 19, "Marbled Colby + Monterey Jack."),
    D("string-cheese", "String cheese", PC, "Semi-soft cheese", ["dairy"], DAIRY,
      298, 2.5, 26, 0, 22, 528, 0.5, 14, "Low-moisture mozzarella in stick form."),
    D("shredded-mexican-blend", "Shredded Mexican-blend cheese", PC, "Shredded cheese",
      ["dairy"], DAIRY,
      372, 1.3, 23, 0, 30, 590, 0.5, 18,
      "Cheddar/Monterey/Asadero/Queso quesadilla blend."),
    D("shredded-italian-blend", "Shredded Italian-blend cheese", PC, "Shredded cheese",
      ["dairy"], DAIRY,
      366, 2.0, 25, 0, 28, 540, 0.5, 17,
      "Mozzarella + provolone + parmesan + asiago blend."),
    D("shredded-cheddar", "Shredded cheddar", PC, "Shredded cheese", ["dairy"], DAIRY,
      404, 1.3, 23, 0, 33, 653, 0.5, 21, "Pre-grated standard cheddar."),
    D("shredded-mozzarella", "Shredded mozzarella", PC, "Shredded cheese", ["dairy"], DAIRY,
      300, 2.2, 22, 0, 22, 627, 1, 13, "Pre-grated low-moisture mozzarella."),
    D("cheez-whiz", "Cheese sauce (Cheez Whiz-style)", PC, "Processed cheese",
      ["dairy"], DAIRY,
      275, 6, 9, 0, 24, 1400, 4, 12,
      "Jarred process-cheese sauce; nacho/pasta use.", form="paste"),
    D("nacho-cheese", "Nacho cheese sauce (canned)", PC, "Processed cheese",
      ["dairy"], DAIRY,
      245, 8, 7, 0.5, 20, 1200, 4, 9,
      "Pumpable cheese sauce for nachos.", form="canned"),
    D("cheese-spread", "Cheese spread (cold pack)", PC, "Processed cheese",
      ["dairy"], DAIRY,
      290, 8, 16, 0, 22, 1300, 6, 14,
      "Cold-pack cheddar spread; tub format.", form="paste"),
]


# ---------------------------------------------------------------------------
# Aged cheese additions (~12)
# ---------------------------------------------------------------------------
AC = "Aged cheese"

AGED = [
    D("havarti", "Havarti", AC, "Aged cheese", ["dairy"], DAIRY,
      371, 3, 23, 0, 30, 685, 0.4, 19, "Danish semi-soft mild cow cheese."),
    D("muenster", "Muenster (American)", AC, "Aged cheese", ["dairy"], DAIRY,
      368, 1.1, 23, 0, 30, 628, 1, 19, "Mild American semi-soft; orange rind."),
    D("limburger", "Limburger", AC, "Aged cheese", ["dairy"], DAIRY,
      327, 0.5, 20, 0, 27, 800, 0.5, 17, "Strong-smelling Belgian washed-rind."),
    D("raclette", "Raclette cheese", AC, "Aged cheese", ["dairy"], DAIRY,
      357, 0.4, 23, 0, 29, 620, 0.4, 19, "Swiss/French melting cheese."),
    D("cambozola", "Cambozola", AC, "Blue cheese", ["dairy"], DAIRY,
      427, 0.5, 14, 0, 41, 658, 0.5, 26, "German triple-cream blue-veined cheese."),
    D("gouda-aged", "Gouda (aged)", AC, "Aged cheese", ["dairy"], DAIRY,
      388, 2.2, 28, 0, 30, 730, 0.7, 19,
      "Aged 1+ year: caramel-crystalline texture, nutty."),
    D("pecorino-toscano", "Pecorino Toscano", AC, "Hard grating cheese", ["dairy"], DAIRY,
      387, 1.6, 27, 0, 30, 1140, 0.5, 19, "Tuscan aged sheep cheese; nuttier than romano."),
    D("romano-cheese", "Romano cheese", AC, "Hard grating cheese", ["dairy"], DAIRY,
      387, 3.7, 32, 0, 27, 1433, 0.7, 17, "Sharp grating cheese; American cow-milk version."),
    D("cheese-curds", "Cheese curds (cheddar)", AC, "Cheddar", ["dairy"], DAIRY,
      403, 1.3, 25, 0, 33, 621, 0.5, 21, "Squeaky fresh cheddar curds; poutine staple."),
    D("gjetost", "Gjetost (Norwegian brown cheese)", AC, "Aged cheese", ["dairy"], DAIRY,
      466, 42, 9, 0, 30, 600, 42, 19, "Caramelized whey cheese; sweet."),
    D("caciocavallo", "Caciocavallo", AC, "Aged cheese", ["dairy"], DAIRY,
      370, 1, 25, 0, 30, 690, 0.5, 19, "Aged Italian stretched-curd cow cheese."),
    D("appenzeller", "Appenzeller", AC, "Aged cheese", ["dairy"], DAIRY,
      403, 0.5, 28, 0, 32, 700, 0.5, 21, "Swiss washed-rind cow cheese."),
]


# ---------------------------------------------------------------------------
# Fresh cheese additions (~6)
# ---------------------------------------------------------------------------
FC = "Fresh cheese"

FRESH = [
    D("chevre", "Chèvre (fresh goat)", FC, "Fresh cheese", ["dairy"], DAIRY,
      264, 2.5, 18, 0, 21, 478, 2.5, 14, "Soft fresh goat cheese log."),
    D("bocconcini", "Bocconcini", FC, "Mozzarella", ["dairy"], DAIRY,
      280, 3, 18, 0, 22, 18, 0.4, 13, "Small fresh mozzarella balls in brine."),
    D("caciotta", "Caciotta", FC, "Fresh cheese", ["dairy"], DAIRY,
      330, 1, 23, 0, 26, 580, 0.5, 16, "Soft young Italian cow/sheep cheese."),
    D("queso-blanco", "Queso blanco", FC, "Fresh cheese", ["dairy"], DAIRY,
      310, 3, 20, 0, 24, 690, 1, 15, "Latin American white cheese; doesn't melt."),
    D("queso-asadero", "Queso asadero", FC, "Stretched curd", ["dairy"], DAIRY,
      350, 1.5, 22, 0, 28, 580, 0.5, 17, "Mexican melting cheese."),
    D("requeson", "Requesón", FC, "Ricotta", ["dairy"], DAIRY,
      174, 3, 11, 0, 13, 84, 0.3, 8, "Mexican-style ricotta from whey."),
]


# ---------------------------------------------------------------------------
# Frozen dairy (~9)
# ---------------------------------------------------------------------------
FZ = "Frozen dairy"

FROZEN = [
    D("ice-cream-chocolate", "Ice cream (chocolate)", FZ, "Ice cream",
      ["dairy", "caffeine"], DAIRY,
      216, 28, 3.8, 1.2, 11, 76, 25, 6.8, "Standard premium-ish chocolate ice cream.",
      form="frozen"),
    D("ice-cream-strawberry", "Ice cream (strawberry)", FZ, "Ice cream", ["dairy"], DAIRY,
      192, 27, 3.2, 0.3, 8.4, 60, 22, 5.2, "Strawberry ice cream.", form="frozen"),
    D("ice-cream-mint-chip", "Ice cream (mint chip)", FZ, "Ice cream",
      ["dairy", "caffeine"], DAIRY,
      221, 25, 3.5, 0.5, 12, 75, 23, 7.5, "Mint + chocolate chip.", form="frozen"),
    D("ice-cream-cookies-cream", "Ice cream (cookies & cream)", FZ, "Ice cream",
      ["dairy", "gluten", "caffeine"], DAIRY,
      223, 28, 4, 0.5, 11, 110, 23, 6.5, "Vanilla base with Oreo-style chunks.", form="frozen"),
    D("frozen-yogurt", "Frozen yogurt (vanilla)", FZ, "Frozen desserts", ["dairy"], DAIRY,
      127, 22, 3, 0, 4, 63, 17, 2.5, "Cultured yogurt frozen dessert.", form="frozen"),
    D("sherbet", "Sherbet (orange)", FZ, "Frozen desserts", ["dairy"], DAIRY,
      144, 30, 1.1, 1.4, 2, 46, 24, 1.2,
      "Light dairy fruit ice; less milk than ice cream.", form="frozen"),
    D("sorbet", "Sorbet", FZ, "Frozen desserts", [], PLANT,
      144, 36, 0.4, 0.4, 0.2, 7, 30, 0.05,
      "Dairy-free fruit ice. Plant channel; carries no dairy tag.", form="frozen"),
    D("gelato-vanilla", "Gelato (vanilla)", FZ, "Ice cream", ["dairy"], DAIRY,
      161, 24, 4, 0, 6, 50, 22, 4, "Italian-style ice cream; lower fat than US.",
      form="frozen"),
    D("ice-cream-sandwich", "Ice cream sandwich", FZ, "Ice cream",
      ["dairy", "gluten", "caffeine"], DAIRY,
      237, 36, 4, 1, 9, 145, 21, 5, "Vanilla ice cream between chocolate wafers.",
      form="frozen"),
    D("frozen-custard", "Frozen custard", FZ, "Ice cream",
      ["dairy", "eggs"], DAIRY,
      222, 22, 5, 0, 13, 80, 21, 7.5, "Egg-yolk-rich slow-churned frozen dessert.",
      form="frozen"),
]


# ---------------------------------------------------------------------------
# Fermented dairy / Milk extras (~10)
# ---------------------------------------------------------------------------
FD = "Fermented dairy"
MK = "Milk"

MILK_AND_FERMENT = [
    D("chocolate-milk", "Chocolate milk", MK, "Cow milk",
      ["dairy", "caffeine"], DAIRY,
      83, 10, 3.2, 0.3, 3.4, 60, 9.5, 2.1, "2% milk + cocoa + sugar."),
    D("strawberry-milk", "Strawberry milk", MK, "Cow milk", ["dairy"], DAIRY,
      72, 11, 3, 0, 2, 58, 11, 1.3, "Strawberry-flavored sweetened milk."),
    D("half-and-half", "Half-and-half", "Cream & butter", "Cream", ["dairy"], DAIRY,
      131, 4.3, 3.1, 0, 11.5, 41, 4.3, 7.2, "Cream + milk; ~10-12% fat."),
    D("light-cream", "Light cream (table cream)", "Cream & butter", "Cream",
      ["dairy"], DAIRY,
      195, 4, 2.7, 0, 19, 40, 4, 12, "~18% fat; for coffee + cooking."),
    D("whipping-cream", "Whipping cream", "Cream & butter", "Cream", ["dairy"], DAIRY,
      292, 2.8, 2.4, 0, 30, 38, 2.8, 19, "~30% fat; whips to soft peaks."),
    D("milk-powder", "Milk powder (whole, dry)", MK, "Concentrated milk", ["dairy"], DAIRY,
      496, 38, 26, 0, 27, 371, 38, 17, "Dehydrated whole milk.", form="powdered"),
    D("milk-powder-nonfat", "Milk powder (nonfat, dry)", MK, "Concentrated milk",
      ["dairy"], DAIRY,
      362, 52, 36, 0, 1, 535, 52, 0.7, "Skim milk dehydrated.", form="powdered"),
    D("malted-milk-powder", "Malted milk powder", MK, "Concentrated milk",
      ["dairy", "gluten"], DAIRY,
      410, 75, 11, 4, 7, 720, 56, 4, "Malted barley + wheat + milk; Ovaltine base.",
      form="powdered"),
    D("yogurt-low-fat", "Yogurt (low-fat, plain)", "Yogurt", "Regular yogurt",
      ["dairy"], DAIRY,
      63, 7, 5.3, 0, 1.6, 70, 7, 1, "Lowfat plain yogurt; standard breakfast option."),
    D("yogurt-fruit", "Yogurt (fruit, sweetened)", "Yogurt", "Regular yogurt",
      ["dairy"], DAIRY,
      102, 19, 4.4, 0, 1.1, 58, 18, 0.7, "Yoplait-style flavored cup yogurt."),
    D("kefir-plain", "Kefir (plain)", FD, "Fermented milk", ["dairy"], DAIRY,
      63, 7, 3.8, 0, 2.5, 52, 4.5, 1.6, "Cultured drinking yogurt-like milk."),
    D("clabber-cream", "Clabber cream / cultured cream", FD, "Cultured milk",
      ["dairy"], DAIRY,
      198, 4.6, 2.8, 0, 19, 80, 4.6, 11.7,
      "Cultured cream; sour-cream-like for baking."),
]


ALL_NEW = PROCESSED + AGED + FRESH + FROZEN + MILK_AND_FERMENT


def main() -> None:
    with ING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    by_id = {ing["id"]: ing for ing in data}

    appended = skipped = 0
    for entry in ALL_NEW:
        if entry["id"] in by_id:
            print(f"  ! skipped — id {entry['id']} already exists", file=sys.stderr)
            skipped += 1
            continue
        gw = entry["group_weights"]
        assert len(gw) == 3 and sum(gw) == 1 and gw.count(1) == 1 and gw.count(0) == 2, \
            f"{entry['id']} violates single-group rule: {gw}"
        assert entry["food_group"] == "Dairy", f"{entry['id']} has food_group={entry['food_group']}"
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
