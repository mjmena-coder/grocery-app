"""
backend/consolidation_engine.py

Consolidates recipe ingredients into a clean, human-friendly grocery list.
Handles unit normalization via Pint, formats quantities into cooking fractions,
and preserves database traceability and audit review flags.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import pint

from backend.models import Ingredient

# =====================================================================
# 1. Pint Unit Registry Configuration
# =====================================================================

ureg = pint.UnitRegistry()

# Custom culinary/count units required so Pint does not throw UndefinedUnitError
CUSTOM_UNITS = [
    "clove = [] = cloves",
    "ear = [] = ears",
    "head = [] = heads",
    "stalk = [] = stalks",
    "bunch = [] = bunches",
    "can = [] = cans",
    "package = [] = packages = pack = packs",
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
# 2. Data Models
# =====================================================================

@dataclass
class ConsolidatedGroup:
    name: str
    source_ingredient_ids: List[int] = field(default_factory=list)
    quantities_by_dimension: Dict[str, float] = field(
        default_factory=lambda: {"volume_ml": 0.0, "mass_g": 0.0}
    )
    count_quantities: Dict[str, float] = field(default_factory=dict)
    no_qty_items: List[int] = field(default_factory=list)
    needs_manual_review: bool = False
    review_reasons: List[str] = field(default_factory=list)


# =====================================================================
# 3. Helpers & Fraction Formatting
# =====================================================================

def _get_ingredient_name(ingredient: Ingredient) -> str:
    """Prefers DB canonical_name; falls back to trimmed lower raw_name."""
    if getattr(ingredient, "canonical_ingredient", None):
        return ingredient.canonical_ingredient.name.strip().lower()
    return ingredient.raw_name.strip().lower()


def _format_quantity_value(val: float) -> str:
    """Converts floats to clean mixed fractions including eighths."""
    if val <= 0:
        return ""
    
    whole = int(val)
    remainder = val - whole
    
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


def _format_volume(ml_val: float) -> Tuple[float, str, str]:
    """Converts mL to human-friendly cooking units and fraction text."""
    qty = ml_val * ureg.milliliter

    # Keep items under 1/2 cup (118 mL / 8 tbsp) in tablespoons/teaspoons
    if ml_val < 118.0:
        tbsp = qty.to("tablespoon").magnitude
        if tbsp < 1.0:
            tsp = qty.to("teaspoon").magnitude
            unit_str = "teaspoon" if round(tsp, 2) == 1.0 else "teaspoons"
            return (round(tsp, 2), unit_str, f"{_format_quantity_value(tsp)} {unit_str}".strip())
        
        unit_str = "tablespoon" if round(tbsp, 2) == 1.0 else "tablespoons"
        return (round(tbsp, 2), unit_str, f"{_format_quantity_value(tbsp)} {unit_str}".strip())

    cups = qty.to("cup").magnitude
    unit_str = "cup" if round(cups, 2) == 1.0 else "cups"
    return (round(cups, 2), unit_str, f"{_format_quantity_value(cups)} {unit_str}".strip())


def _format_mass(g_val: float) -> Tuple[float, str, str]:
    """Converts grams to human-friendly cooking units and fraction text."""
    qty = g_val * ureg.gram
    
    if g_val >= 450.0:
        lbs = qty.to("pound").magnitude
        unit_str = "pound" if round(lbs, 2) == 1.0 else "pounds"
        return (round(lbs, 2), unit_str, f"{_format_quantity_value(lbs)} {unit_str}".strip())

    oz = qty.to("ounce").magnitude
    unit_str = "ounce" if round(oz, 2) == 1.0 else "ounces"
    return (round(oz, 2), unit_str, f"{_format_quantity_value(oz)} {unit_str}".strip())


# =====================================================================
# 4. Core Consolidation Engine
# =====================================================================

def consolidate_ingredients(ingredients: List[Ingredient]) -> List[Dict]:
    """
    Main entry point: Aggregates ingredients into a consolidated grocery list.
    """
    groups: Dict[str, ConsolidatedGroup] = {}

    for ingredient in ingredients:
        name = _get_ingredient_name(ingredient)

        if name not in groups:
            # Create new item in consolidated group.
            groups[name] = ConsolidatedGroup(name=name)

        grp = groups[name]
        if hasattr(ingredient, "id") and ingredient.id is not None:
            grp.source_ingredient_ids.append(ingredient.id)

        # Preserve upstream audit/review flags
        if getattr(ingredient, "needs_manual_review", False):
            grp.needs_manual_review = True
            reason = getattr(ingredient, "review_reason", None)
            if reason and reason not in grp.review_reasons:
                grp.review_reasons.append(reason)

        # Case 1: Zero quantity / "to taste" items
        if ingredient.quantity is None:
            if hasattr(ingredient, "id") and ingredient.id is not None:
                grp.no_qty_items.append(ingredient.id)
            continue # serves as a break, next ingredient.

        # Case 2: Unspecified unit (discrete count)
        if not ingredient.unit:
            grp.count_quantities[""] = (
                grp.count_quantities.get("", 0.0) + ingredient.quantity
            )
            continue # serves as a break, next ingredient.

        unit_str = ingredient.unit.strip().lower()

        # Case 3: Parse unit directly with Pint
        try:
            pint_qty = ingredient.quantity * ureg(unit_str)
            if pint_qty.check("[volume]"):
                grp.quantities_by_dimension["volume_ml"] += pint_qty.to("milliliter").magnitude
            elif pint_qty.check("[mass]"):
                grp.quantities_by_dimension["mass_g"] += pint_qty.to("gram").magnitude
            else:
                # Some other quantity that is not volume or mass.
                u_name = str(pint_qty.units)
                grp.count_quantities[u_name] = (
                    grp.count_quantities.get(u_name, 0.0) + ingredient.quantity
                )
        except Exception:
            grp.count_quantities[unit_str] = (
                grp.count_quantities.get(unit_str, 0.0) + ingredient.quantity
            )

    # =====================================================================
    # 5. Output Construction
    # =====================================================================

    output = []

    for name, grp in groups.items():
        out_quantity: Optional[float] = None
        out_unit: Optional[str] = None
        display_parts = []

        # 1. Volume aggregation
        vol_ml = grp.quantities_by_dimension["volume_ml"]
        if vol_ml > 0:
            qty_val, unit_name, display_str = _format_volume(vol_ml)
            out_quantity, out_unit = qty_val, unit_name
            display_parts.append(display_str)

        # 2. Mass aggregation
        mass_g = grp.quantities_by_dimension["mass_g"]
        if mass_g > 0:
            qty_val, unit_name, display_str = _format_mass(mass_g)
            out_quantity = qty_val if out_quantity is None else out_quantity
            out_unit = unit_name if out_unit is None else out_unit
            display_parts.append(display_str)

        # 3. Discrete count items
        for u_name, count_val in grp.count_quantities.items():
            out_quantity = count_val if out_quantity is None else out_quantity
            formatted_count = _format_quantity_value(count_val)

            if u_name:
                u_display = u_name if count_val <= 1.0 or u_name.endswith("s") else f"{u_name}s" # Plurify.
                out_unit = u_display if out_unit is None else out_unit # If vol or mass, use its unit
                display_parts.append(f"{formatted_count} {u_display}".strip())
            else:
                display_parts.append(formatted_count)

        # Construct final display string
        if display_parts:
            formatted_qty_str = " + ".join(display_parts)
            display_text = f"{formatted_qty_str}".strip()
        else:
            display_text = grp.name.capitalize()

        review_reason = (
            "; ".join(grp.review_reasons) if grp.needs_manual_review else None
        )

        output.append(
            {
                "name": grp.name,
                "quantity": out_quantity,
                "unit": out_unit,
                "display_text": display_text,
                "source_ingredient_ids": grp.source_ingredient_ids,
                "needs_manual_review": grp.needs_manual_review,
                "review_reason": review_reason,
            }
        )

    return output