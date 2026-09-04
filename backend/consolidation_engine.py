"""
backend/consolidation_engine.py

Redesigned grocery consolidation engine:
- Normalizes unit descriptors (large, small, etc.) so counts aggregate cleanly.
- Converts culinary measurements (cups, tbsp, oz) of produce/staples into whole store purchase quantities.
- Generates both practical shopping estimates (display_text) and exact recipe sums (original_display_text).
"""

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import pint

from backend.models import Ingredient

# =====================================================================
# 1. Pint Unit Registry Configuration
# =====================================================================

ureg = pint.UnitRegistry()

CUSTOM_UNITS = [
    "clove = [] = cloves",
    "ear = [] = ears",
    "head = [] = heads",
    "stalk = [] = stalks = rib = ribs",
    "bunch = [] = bunches",
    "can = [] = cans",
    "package = [] = packages = pack = packs = container = containers",
    "pinch = 0.0625 * teaspoon = pinches",
    "dash = 0.125 * teaspoon = dashes",
    "drop = 0.02 * teaspoon = drops",
    "slice = [] = slices",
    "piece = [] = pieces",
    "stick = 0.5 * cup = sticks",
]

for unit_def in CUSTOM_UNITS:
    try:
        ureg.define(unit_def)
    except pint.errors.RedefinedUnitError:
        pass


# =====================================================================
# 2. Culinary & Produce Conversions Table
# =====================================================================

PRODUCE_CONVERSIONS = {
    "onion": {"unit": "onion", "ml_per_count": 236.59, "round_strategy": "ceil"},
    "yellow onion": {"unit": "yellow onion", "ml_per_count": 236.59, "round_strategy": "ceil"},
    "red onion": {"unit": "red onion", "ml_per_count": 236.59, "round_strategy": "ceil"},
    "white onion": {"unit": "white onion", "ml_per_count": 236.59, "round_strategy": "ceil"},
    "sweet onion": {"unit": "sweet onion", "ml_per_count": 236.59, "round_strategy": "ceil"},
    "shallot": {"unit": "shallot", "ml_per_count": 45.0, "round_strategy": "ceil"},
    "bell pepper": {"unit": "bell pepper", "ml_per_count": 236.59, "round_strategy": "ceil"},
    "green bell pepper": {"unit": "green bell pepper", "ml_per_count": 236.59, "round_strategy": "ceil"},
    "red bell pepper": {"unit": "red bell pepper", "ml_per_count": 236.59, "round_strategy": "ceil"},
    "carrot": {"unit": "carrot", "ml_per_count": 118.29, "g_per_count": 60.0, "round_strategy": "ceil"},
    "celery": {"unit": "stalk", "ml_per_count": 118.29, "round_strategy": "ceil"},
    "lemon": {"unit": "lemon", "ml_per_count": 45.0, "round_strategy": "ceil"},
    "lime": {"unit": "lime", "ml_per_count": 30.0, "round_strategy": "ceil"},
    "garlic": {"unit": "clove", "ml_per_count": 4.93, "round_strategy": "ceil"},
    "garlic clove": {"unit": "clove", "ml_per_count": 4.93, "round_strategy": "ceil"},
    "egg": {"unit": "egg", "round_strategy": "ceil"},
    "cilantro": {"unit": "bunch", "default_qty": 1},
    "parsley": {"unit": "bunch", "default_qty": 1},
    "fresh parsley": {"unit": "bunch", "default_qty": 1},
    "fresh cilantro": {"unit": "bunch", "default_qty": 1},
    "basil": {"unit": "pack", "default_qty": 1},
    "fresh basil": {"unit": "pack", "default_qty": 1},
    "ginger": {"unit": "piece", "default_qty": 1},
    "scallion": {"unit": "bunch", "default_qty": 1},
    "green onion": {"unit": "bunch", "default_qty": 1},
}

SIZE_DESCRIPTORS = {
    "large", "medium", "small", "extra large", "xl", "tiny", "big",
    "chopped", "minced", "diced", "sliced", "fresh", "crushed", "heaping"
}


# =====================================================================
# 3. Helpers
# =====================================================================

def _normalize_unit(unit_str: Optional[str]) -> Tuple[Optional[str], float]:
    """Cleans unit strings and strips size descriptors."""
    if not unit_str:
        return None, 1.0
    
    clean = unit_str.strip().lower()
    for desc in sorted(SIZE_DESCRIPTORS, key=len, reverse=True):
        clean = re.sub(rf"\b{re.escape(desc)}\b", "", clean).strip()

    singular_map = {
        "cloves": "clove",
        "heads": "head",
        "ears": "ear",
        "stalks": "stalk",
        "ribs": "stalk",
        "rib": "stalk",
        "bunches": "bunch",
        "cans": "can",
        "packages": "package",
        "packs": "package",
        "pack": "package",
        "slices": "slice",
        "pieces": "piece",
        "sticks": "stick",
        "onions": "onion",
        "lemons": "lemon",
        "limes": "lime",
        "carrots": "carrot",
        "eggs": "egg",
        "cups": "cup",
        "tablespoons": "tablespoon",
        "tbsp": "tablespoon",
        "teaspoons": "teaspoon",
        "tsp": "teaspoon",
        "ounces": "ounce",
        "oz": "ounce",
        "pounds": "pound",
        "lbs": "pound",
        "lb": "pound",
    }
    clean = singular_map.get(clean, clean)
    return (clean if clean else None), 1.0


def _get_ingredient_name(ingredient: Ingredient) -> str:
    if getattr(ingredient, "canonical_ingredient", None):
        return ingredient.canonical_ingredient.name.strip().lower()
    return ingredient.raw_name.strip().lower()


def _format_quantity_fraction(val: float) -> str:
    if val <= 0:
        return ""
    whole = int(val)
    remainder = round(val - whole, 3)
    if remainder < 0.08:
        frac_str = ""
    elif remainder < 0.19:
        frac_str = "1/8"
    elif remainder < 0.29:
        frac_str = "1/4"
    elif remainder < 0.355:
        frac_str = "1/3"
    elif remainder < 0.437:
        frac_str = "3/8"
    elif remainder < 0.562:
        frac_str = "1/2"
    elif remainder < 0.645:
        frac_str = "5/8"
    elif remainder < 0.71:
        frac_str = "2/3"
    elif remainder < 0.812:
        frac_str = "3/4"
    elif remainder < 0.937:
        frac_str = "7/8"
    else:
        whole += 1
        frac_str = ""

    if whole > 0 and frac_str:
        return f"{whole} {frac_str}"
    elif whole > 0:
        return str(whole)
    return frac_str if frac_str else "1"


def _pluralize_unit(unit: str, count: float) -> str:
    if count <= 1.0:
        return unit
    plurals = {
        "clove": "cloves",
        "head": "heads",
        "ear": "ears",
        "stalk": "stalks",
        "bunch": "bunches",
        "can": "cans",
        "package": "packages",
        "pack": "packs",
        "slice": "slices",
        "piece": "pieces",
        "stick": "sticks",
        "onion": "onions",
        "yellow onion": "yellow onions",
        "red onion": "red onions",
        "white onion": "white onions",
        "sweet onion": "sweet onions",
        "shallot": "shallots",
        "bell pepper": "bell peppers",
        "green bell pepper": "green bell peppers",
        "red bell pepper": "red bell peppers",
        "carrot": "carrots",
        "lemon": "lemons",
        "lime": "limes",
        "egg": "eggs",
        "cup": "cups",
        "tablespoon": "tablespoons",
        "teaspoon": "teaspoons",
        "ounce": "ounces",
        "pound": "pounds",
    }
    return plurals.get(unit, f"{unit}s")


# =====================================================================
# 4. Data Models & Consolidation
# =====================================================================

@dataclass
class ConsolidatedGroup:
    name: str
    source_ingredient_ids: List[int] = field(default_factory=list)
    vol_ml: float = 0.0
    mass_g: float = 0.0
    counts: Dict[str, float] = field(default_factory=dict)
    unmeasured: bool = False
    needs_manual_review: bool = False
    review_reasons: List[str] = field(default_factory=list)


def consolidate_ingredients(ingredients: List[Ingredient]) -> List[Dict]:
    groups: Dict[str, ConsolidatedGroup] = {}

    for ing in ingredients:
        name = _get_ingredient_name(ing)
        if name not in groups:
            groups[name] = ConsolidatedGroup(name=name)
        grp = groups[name]

        if hasattr(ing, "id") and ing.id is not None:
            grp.source_ingredient_ids.append(ing.id)

        if getattr(ing, "needs_manual_review", False):
            grp.needs_manual_review = True
            reason = getattr(ing, "review_reason", None)
            if reason and reason not in grp.review_reasons:
                grp.review_reasons.append(reason)

        if ing.quantity is None:
            grp.unmeasured = True
            continue

        raw_unit, multiplier = _normalize_unit(ing.unit)
        qty = ing.quantity * multiplier

        if not raw_unit:
            grp.counts[""] = grp.counts.get("", 0.0) + qty
            continue

        try:
            p_qty = qty * ureg(raw_unit)
            if p_qty.check("[volume]"):
                grp.vol_ml += p_qty.to("milliliter").magnitude
            elif p_qty.check("[mass]"):
                grp.mass_g += p_qty.to("gram").magnitude
            else:
                grp.counts[raw_unit] = grp.counts.get(raw_unit, 0.0) + qty
        except Exception:
            grp.counts[raw_unit] = grp.counts.get(raw_unit, 0.0) + qty

    output = []

    for name, grp in groups.items():
        exact_parts = []
        
        # 1. Exact Recipe Measurement
        if grp.vol_ml > 0:
            qty_vol = grp.vol_ml * ureg.milliliter
            if grp.vol_ml < 118.0:
                tbsp = qty_vol.to("tablespoon").magnitude
                if tbsp < 1.0:
                    tsp = qty_vol.to("teaspoon").magnitude
                    exact_parts.append(f"{_format_quantity_fraction(tsp)} {_pluralize_unit('teaspoon', tsp)}")
                else:
                    exact_parts.append(f"{_format_quantity_fraction(tbsp)} {_pluralize_unit('tablespoon', tbsp)}")
            else:
                cups = qty_vol.to("cup").magnitude
                exact_parts.append(f"{_format_quantity_fraction(cups)} {_pluralize_unit('cup', cups)}")

        if grp.mass_g > 0:
            qty_mass = grp.mass_g * ureg.gram
            if grp.mass_g >= 450.0:
                lbs = qty_mass.to("pound").magnitude
                exact_parts.append(f"{_format_quantity_fraction(lbs)} {_pluralize_unit('pound', lbs)}")
            else:
                oz = qty_mass.to("ounce").magnitude
                exact_parts.append(f"{_format_quantity_fraction(oz)} {_pluralize_unit('ounce', oz)}")

        for u, count in grp.counts.items():
            f_cnt = _format_quantity_fraction(count)
            if u:
                exact_parts.append(f"{f_cnt} {_pluralize_unit(u, count)}")
            else:
                exact_parts.append(f"{f_cnt}")

        exact_display = " + ".join(exact_parts) if exact_parts else ""

        # 2. Grocery Shopping Smart Estimate
        rule = PRODUCE_CONVERSIONS.get(name)
        shopping_display = ""
        out_quantity: Optional[float] = None
        out_unit: Optional[str] = None

        if rule:
            target_unit = rule.get("unit", "")
            converted_counts = 0.0

            if rule.get("ml_per_count") and grp.vol_ml > 0:
                converted_counts += grp.vol_ml / rule["ml_per_count"]

            if rule.get("g_per_count") and grp.mass_g > 0:
                converted_counts += grp.mass_g / rule["g_per_count"]

            for u, count in grp.counts.items():
                if u in ("", target_unit, _pluralize_unit(target_unit, 2)):
                    converted_counts += count

            if converted_counts > 0:
                if rule.get("round_strategy") == "ceil":
                    final_count = float(math.ceil(round(converted_counts, 2)))
                else:
                    final_count = round(converted_counts, 1)
                out_quantity = final_count
                out_unit = target_unit
                shopping_display = f"{int(final_count) if final_count.is_integer() else final_count} {_pluralize_unit(target_unit, final_count)}"
            elif rule.get("default_qty"):
                out_quantity = float(rule["default_qty"])
                out_unit = target_unit
                shopping_display = f"{rule['default_qty']} {_pluralize_unit(target_unit, rule['default_qty'])}"

        if not shopping_display:
            shopping_display = exact_display

        review_reason = "; ".join(grp.review_reasons) if grp.needs_manual_review else None

        output.append({
            "name": grp.name,
            "quantity": out_quantity,
            "unit": out_unit,
            "display_text": shopping_display,
            "original_display_text": exact_display,
            "source_ingredient_ids": grp.source_ingredient_ids,
            "needs_manual_review": grp.needs_manual_review,
            "review_reason": review_reason,
        })

    return output
