"""
backend/consolidation_engine.py

Consolidates recipe ingredients into a clean, human-friendly grocery list.
Handles unit normalization via Pint, standardizes item names, and formats quantities.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Tuple
import pint

# =====================================================================
# 1. Pint Unit Registry Configuration
# =====================================================================

ureg = pint.UnitRegistry()

# Register custom culinary/count units not natively in Pint
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
    "stick = 0.5 * cup = sticks",  # 1 stick of butter = 8 tbsp = 0.5 cup
]

for unit_def in CUSTOM_UNITS:
    try:
        ureg.define(unit_def)
    except pint.errors.RedefinedUnitError:
        pass

# Size adjectives to strip before passing units to Pint
SIZE_ADJECTIVES = re.compile(
    r"\b(small|medium|large|extra-large|xl|jumbo|tiny|big)\b", re.IGNORECASE
)

# Words to strip from raw ingredient names to get canonical names
PREP_WORDS = re.compile(
    r"\b(chopped|diced|minced|sliced|peeled|grated|shredded|fresh|cooked|raw|"
    r"frozen|canned|drained|rinsed|halved|quartered|cubed|crushed|ground|"
    r"flat-leaf|flat-leaves|flat leaf|flat leaves|curly)\b",
    re.IGNORECASE,
)


# =====================================================================
# 2. Data Models
# =====================================================================


@dataclass
class IngredientInput:
    id: int
    raw_name: str
    quantity: Optional[float]
    unit: Optional[str]
    needs_manual_review: bool = False
    review_reason: Optional[str] = None


@dataclass
class ConsolidatedGroup:
    canonical_name: str
    source_ingredient_ids: List[int] = field(default_factory=list)
    quantities_by_dimension: Dict[str, float] = field(
        default_factory=lambda: {"volume_ml": 0.0, "mass_g": 0.0}
    )
    count_quantities: Dict[str, float] = field(default_factory=dict)
    no_qty_items: List[int] = field(default_factory=list)
    modifiers: set = field(default_factory=set)
    needs_manual_review: bool = False
    review_reasons: List[str] = field(default_factory=list)


# =====================================================================
# 3. Text Normalization & Unit Cleaning
# =====================================================================


def _normalize_name(name: str) -> str:
    """Normalizes raw ingredient names for canonical matching."""
    cleaned = PREP_WORDS.sub("", name.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else name.lower().strip()


def _clean_unit_str(unit_str: str) -> Tuple[str, str]:
    """
    Separates size adjectives from units for Pint lookups.
    Example: 'large cloves' -> ('cloves', 'large')
    """
    match = SIZE_ADJECTIVES.search(unit_str)
    modifier = match.group(0).lower() if match else ""
    cleaned_unit = SIZE_ADJECTIVES.sub("", unit_str).strip()
    return (cleaned_unit if cleaned_unit else unit_str), modifier


def _parse_pint_quantity(quantity: float, unit: str) -> Optional[pint.Quantity]:
    """Attempts to convert quantity + unit string into a Pint Quantity."""
    clean_unit, _ = _clean_unit_str(unit)
    try:
        return quantity * ureg(clean_unit)
    except (pint.errors.UndefinedUnitError, AttributeError):
        return None


# =====================================================================
# 4. Quantity Formatting & Thresholding
# =====================================================================


def _format_volume(ml_val: float) -> Tuple[float, str]:
    """Converts volume in mL to human-friendly cooking units."""
    qty = ml_val * ureg.milliliter

    # Less than 3 tbsp (45 ml) -> Display in teaspoons / tablespoons
    if ml_val < 45.0:
        tbsp = qty.to("tablespoon").magnitude
        if tbsp < 1.0:
            tsp = round(qty.to("teaspoon").magnitude, 2)
            return (tsp, "teaspoon" if tsp == 1.0 else "teaspoons")
        tbsp_rounded = round(tbsp, 2)
        return (tbsp_rounded, "tablespoon" if tbsp_rounded == 1.0 else "tablespoons")

    # 45 mL or more -> Display in cups
    cups = round(qty.to("cup").magnitude, 2)
    return (cups, "cup" if cups == 1.0 else "cups")


def _format_mass(g_val: float) -> Tuple[float, str]:
    """Converts mass in grams to human-friendly cooking units."""
    qty = g_val * ureg.gram
    # 454g ~ 1 lb
    if g_val >= 450.0:
        lbs = round(qty.to("pound").magnitude, 2)
        return (lbs, "pound" if lbs == 1.0 else "pounds")

    oz = round(qty.to("ounce").magnitude, 2)
    return (oz, "ounce" if oz == 1.0 else "ounces")


# =====================================================================
# 5. Core Consolidation Engine
# =====================================================================


def consolidate_ingredients(
    ingredients: List[IngredientInput],
) -> List[Dict]:
    """
    Main entry point: Aggregates a list of ingredients into a consolidated grocery list.
    """
    groups: Dict[str, ConsolidatedGroup] = {}

    for ing in ingredients:
        canonical = _normalize_name(ing.raw_name)

        if canonical not in groups:
            groups[canonical] = ConsolidatedGroup(canonical_name=canonical)

        grp = groups[canonical]
        grp.source_ingredient_ids.append(ing.id)

        # Retain upstream manual review flags (e.g., OCR or ambiguity flags)
        if ing.needs_manual_review:
            grp.needs_manual_review = True
            if ing.review_reason and ing.review_reason not in grp.review_reasons:
                grp.review_reasons.append(ing.review_reason)

        # Case 1: No quantity provided
        if ing.quantity is None:
            grp.no_qty_items.append(ing.id)
            continue

        # Case 2: Quantity provided without unit (Count items e.g., "2 cucumbers")
        if not ing.unit:
            grp.count_quantities[""] = (
                grp.count_quantities.get("", 0.0) + ing.quantity
            )
            continue

        # Extract size adjectives (e.g., 'large' from 'large cloves')
        clean_unit, modifier = _clean_unit_str(ing.unit)
        if modifier:
            grp.modifiers.add(modifier)

        pint_qty = _parse_pint_quantity(ing.quantity, clean_unit)

        # Case 3: Unit not recognized by Pint -> Treat as count unit
        if pint_qty is None:
            grp.count_quantities[ing.unit] = (
                grp.count_quantities.get(ing.unit, 0.0) + ing.quantity
            )
            continue

        # Case 4: Standard Pint unit -> Convert to base metric for aggregation
        try:
            if pint_qty.check("[volume]"):
                ml = pint_qty.to("milliliter").magnitude
                grp.quantities_by_dimension["volume_ml"] += ml
            elif pint_qty.check("[mass]"):
                grams = pint_qty.to("gram").magnitude
                grp.quantities_by_dimension["mass_g"] += grams
            else:
                # Custom discrete unit (cloves, ears, slices, etc.)
                unit_name = str(pint_qty.units)
                grp.count_quantities[unit_name] = (
                    grp.count_quantities.get(unit_name, 0.0) + ing.quantity
                )
        except Exception:
            grp.count_quantities[ing.unit] = (
                grp.count_quantities.get(ing.unit, 0.0) + ing.quantity
            )

    # =====================================================================
    # 6. Formatting Consolidated Output
    # =====================================================================

    output = []

    for canonical, grp in groups.items():
        out_quantity: Optional[float] = None
        out_unit: Optional[str] = None
        display_parts = []

        # 1. Volume
        vol_ml = grp.quantities_by_dimension["volume_ml"]
        if vol_ml > 0:
            out_quantity, out_unit = _format_volume(vol_ml)
            display_parts.append(f"{out_quantity} {out_unit}")

        # 2. Mass
        mass_g = grp.quantities_by_dimension["mass_g"]
        if mass_g > 0:
            qty, unit = _format_mass(mass_g)
            out_quantity = qty if out_quantity is None else out_quantity
            out_unit = unit if out_unit is None else out_unit
            display_parts.append(f"{qty} {unit}")

        # 3. Discrete Counts / Custom Units
        for u_name, count_val in grp.count_quantities.items():
            count_val = round(count_val, 2)
            out_quantity = count_val if out_quantity is None else out_quantity

            # Re-attach preserved modifiers (e.g., '2.0 large cloves')
            mod_prefix = f"{' '.join(sorted(grp.modifiers))} " if grp.modifiers else ""

            if u_name:
                # Pluralize discrete custom units when quantity > 1.0
                # (e.g., '1.0 large clove' vs '2.0 large cloves')
                unit_str = u_name
                if count_val > 1.0 and not unit_str.endswith("s"):
                    unit_str = f"{unit_str}s"

                unit_disp = f"{mod_prefix}{unit_str}".strip()
                out_unit = unit_disp if out_unit is None else out_unit
                display_parts.append(f"{count_val} {unit_disp}")
            else:
                out_unit = f"{mod_prefix}".strip() if mod_prefix else None
                display_parts.append(f"{count_val} {mod_prefix}".strip())

        # Construct final display string
        if display_parts:
            formatted_qty_str = " + ".join(display_parts)
            display_text = f"{formatted_qty_str} {grp.canonical_name}".strip()
        else:
            display_text = grp.canonical_name.capitalize()

        # Build review reason string if flagged
        review_reason = (
            "; ".join(grp.review_reasons) if grp.needs_manual_review else None
        )

        output.append(
            {
                "canonical_name": grp.canonical_name,
                "quantity": out_quantity,
                "unit": out_unit,
                "display_text": display_text,
                "source_ingredient_ids": grp.source_ingredient_ids,
                "needs_manual_review": grp.needs_manual_review,
                "review_reason": review_reason,
            }
        )

    return output