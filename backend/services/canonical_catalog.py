from typing import Optional, Tuple

# Static seed mapping: normalized_name -> (category, is_dirty_dozen)
CANONICAL_SEED_CATALOG: dict[str, Tuple[str, bool]] = {
    # PRODUCE
    "garlic": ("PRODUCE", False),
    "onion": ("PRODUCE", False),
    "yellow onion": ("PRODUCE", False),
    "red onion": ("PRODUCE", False),
    "kalamata olives": ("PRODUCE", False),
    "olives": ("PRODUCE", False),
    "lemon": ("PRODUCE", False),
    "lime": ("PRODUCE", False),
    "cilantro": ("PRODUCE", False),
    "parsley": ("PRODUCE", False),
    "spinach": ("PRODUCE", True),
    "strawberries": ("PRODUCE", True),
    "kale": ("PRODUCE", True),
    "bell pepper": ("PRODUCE", True),
    "apples": ("PRODUCE", True),
    "grapes": ("PRODUCE", True),
    
    # PANTRY & SPICES
    "cumin": ("PANTRY", False),
    "ground cumin": ("PANTRY", False),
    "paprika": ("PANTRY", False),
    "smoked paprika": ("PANTRY", False),
    "black pepper": ("PANTRY", False),
    "salt": ("PANTRY", False),
    "kosher salt": ("PANTRY", False),
    "olive oil": ("PANTRY", False),
    "extra-virgin olive oil": ("PANTRY", False),
    "flour": ("PANTRY", False),
    "sugar": ("PANTRY", False),
    "oregano": ("PANTRY", False),
    "chili powder": ("PANTRY", False),
    
    # MEAT & PROTEIN
    "chicken breast": ("MEAT", False),
    "chicken thigh": ("MEAT", False),
    "ground beef": ("MEAT", False),
    "bacon": ("MEAT", False),
    "pork chop": ("MEAT", False),
    "salmon": ("MEAT", False),
    "shrimp": ("MEAT", False),
    
    # DAIRY
    "butter": ("DAIRY", False),
    "unsalted butter": ("DAIRY", False),
    "milk": ("DAIRY", False),
    "heavy cream": ("DAIRY", False),
    "parmesan cheese": ("DAIRY", False),
    "cheddar cheese": ("DAIRY", False),
    "eggs": ("DAIRY", False),
}

# Words that GUARANTEE an item is Pantry/Spice regardless of words like "smoked"
PANTRY_OVERRIDE_KEYWORDS = {
    "paprika", "cumin", "pepper", "salt", "powder", "extract",
    "spice", "seasoning", "dried", "flour", "sugar", "oil", "vinegar"
}


def resolve_canonical_category(
    name: str,
    raw_text: str = "",
    vlm_category: Optional[str] = None,
    vlm_dirty_dozen: bool = False
) -> Tuple[str, bool]:
    """
    Determines true Category and Dirty Dozen flag using a strict priority ladder:
    1. Exact match in Seed Catalog
    2. Substring match in Seed Catalog
    3. Pantry / Spice Keyword Overrides
    4. VLM suggestion (if non-GENERAL)
    5. Default to GENERAL
    """
    clean_name = name.strip().lower()
    clean_raw = raw_text.strip().lower()

    # 1. Exact catalog match
    if clean_name in CANONICAL_SEED_CATALOG:
        return CANONICAL_SEED_CATALOG[clean_name]

    # 2. Partial / Substring catalog match (longest matching term wins)
    matching_keys = [k for k in CANONICAL_SEED_CATALOG if k in clean_name or k in clean_raw]
    if matching_keys:
        best_match = max(matching_keys, key=len)
        return CANONICAL_SEED_CATALOG[best_match]

    # 3. Spice & Pantry Keyword Overrides (Prevents "smoked paprika" -> MEAT)
    if any(kw in clean_name or kw in clean_raw for kw in PANTRY_OVERRIDE_KEYWORDS):
        return "PANTRY", False

    # 4. Fallback to VLM category if valid and not GENERAL
    if vlm_category and vlm_category.upper() not in {"GENERAL", "UNKNOWN"}:
        return vlm_category.upper(), vlm_dirty_dozen

    # 5. Ultimate Fallback
    return "GENERAL", vlm_dirty_dozen