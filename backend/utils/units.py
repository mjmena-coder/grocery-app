import re
from typing import Optional, Tuple

# Standardized unit synonyms mapping
UNIT_SYNONYMS: dict[str, str] = {
    # Volume
    "teaspoon": "tsp", "teaspoons": "tsp", "tsp": "tsp", "t": "tsp", "tsps": "tsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "tbsp": "tbsp", "tbs": "tbsp", "tb": "tbsp", "T": "tbsp",
    "cup": "cup", "cups": "cup", "c": "cup",
    "fluid ounce": "fl oz", "fluid ounces": "fl oz", "fl oz": "fl oz", "fl. oz.": "fl oz",
    "pint": "pt", "pints": "pt", "pt": "pt",
    "quart": "qt", "quarts": "qt", "qt": "qt",
    "gallon": "gal", "gallons": "gal", "gal": "gal",
    "milliliter": "ml", "milliliters": "ml", "ml": "ml",
    "liter": "l", "liters": "l", "l": "l",

    # Weight
    "ounce": "oz", "ounces": "oz", "oz": "oz", "ozs": "oz",
    "pound": "lb", "pounds": "lb", "lb": "lb", "lbs": "lb",
    "gram": "g", "grams": "g", "g": "g",
    "kilogram": "kg", "kilograms": "kg", "kg": "kg",

    # Count / Produce / Packaging
    "clove": "clove", "cloves": "clove",
    "head": "head", "heads": "head",
    "can": "can", "cans": "can", "tin": "can", "tins": "can",
    "bunch": "bunch", "bunches": "bunch",
    "sprig": "sprig", "sprigs": "sprig",
    "slice": "slice", "slices": "slice",
    "stalk": "stalk", "stalks": "stalk",
    "pinch": "pinch", "pinches": "pinch",
    "dash": "dash", "dashes": "dash",
    "handful": "handful", "handfuls": "handful",
    "package": "pkg", "packages": "pkg", "pkg": "pkg", "pkgs": "pkg", "packet": "pkg",
    "container": "container", "containers": "container",
    "piece": "piece", "pieces": "piece", "pc": "piece", "pcs": "piece",
}

SIZE_ADJECTIVES = re.compile(
    r"\b(small|smalls|medium|mediums|large|larges|extra-large|xl|jumbo|tiny|big|whole|sliced|diced|chopped|minced|halved)\b",
    re.IGNORECASE,
)

RESCUE_UNITS_REGEX = re.compile(
    r"\b(cloves?|heads?|cans?|bunches?|sprigs?|slices?|stalks?|pinches?|dashes?|pkgs?|packages?)\b",
    re.IGNORECASE,
)


def clean_unit_str(unit_str: Optional[str], raw_text: str = "") -> Tuple[str, str]:
    """
    Extracts size adjectives as modifiers, rescues missing units from raw_text, 
    and normalizes units to standard abbreviations.
    
    Returns:
        Tuple[clean_unit, modifier]
    """
    raw_unit = (unit_str or "").strip().lower()

    # 1. Extract size adjectives / descriptors
    modifier = ""
    match = SIZE_ADJECTIVES.search(raw_unit)
    if match:
        modifier = match.group(0).lower()
        if modifier in {"mediums", "larges", "smalls"}:
            modifier = modifier[:-1]
        raw_unit = SIZE_ADJECTIVES.sub("", raw_unit).strip()

    # 2. Unit Rescue: If unit is empty or was just a size adjective
    if not raw_unit and raw_text:
        rescue_match = RESCUE_UNITS_REGEX.search(raw_text)
        if rescue_match:
            raw_unit = rescue_match.group(0).lower()

    # 3. Standardize unit via synonym catalog
    canonical_unit = UNIT_SYNONYMS.get(raw_unit, raw_unit)

    return canonical_unit, modifier


def adjust_unit_plurality(text: str) -> str:
    """Adjusts basic ingredient quantity units for singular vs plural matching leading numbers."""
    match = re.match(r"^(\d+(?:\.\d+)?)\s*(.*)$", text.strip())
    if not match:
        return text
    val_str, rest = match.groups()
    try:
        val = float(val_str)
    except ValueError:
        return text

    units_map = {
        "cup": "cups", "cups": "cups",
        "clove": "cloves", "cloves": "cloves",
        "tablespoon": "tablespoons", "tablespoons": "tablespoons", "tbsp": "tbsp",
        "teaspoon": "teaspoons", "teaspoons": "teaspoons", "tsp": "tsp",
        "ounce": "ounces", "ounces": "ounces", "oz": "oz",
        "pound": "pounds", "pounds": "pounds", "lb": "lbs", "lbs": "lbs",
        "gram": "grams", "grams": "grams", "g": "g",
        "kilogram": "kilograms", "kilograms": "kilograms", "kg": "kg",
        "can": "cans", "cans": "cans",
        "bunch": "bunches", "bunches": "bunches",
        "head": "heads", "heads": "heads",
        "slice": "slices", "slices": "slices",
        "pinch": "pinches", "pinches": "pinches",
        "dash": "dashes", "dashes": "dashes",
    }

    words = rest.split()
    if words:
        first_word = words[0].lower()
        if first_word in units_map:
            base_unit = units_map[first_word]
            if val == 1.0:
                if base_unit.endswith("es") and base_unit not in ("dashes", "pinches", "bunches"):
                    singular = base_unit[:-2]
                elif base_unit.endswith("s") and base_unit not in ("oz", "lbs"):
                    singular = base_unit[:-1]
                elif base_unit in ("bunches", "pinches", "dashes"):
                    singular = base_unit[:-2]
                else:
                    singular = base_unit
                words[0] = singular
            else:
                words[0] = base_unit
            return f"{val_str} {' '.join(words)}"

    return text
