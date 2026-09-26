import re
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
    "organic lemon": ("PRODUCE", True),
    "lemon zest": ("PRODUCE", True),
    "lime": ("PRODUCE", False),
    "cilantro": ("PRODUCE", False),
    "parsley": ("PRODUCE", False),
    "spinach": ("PRODUCE", True),
    "strawberries": ("PRODUCE", True),
    "strawberries": ("PRODUCE", True),
    "kale": ("PRODUCE", True),
    "collard": ("PRODUCE", True),
    "grape": ("PRODUCE", True),
    "grapes": ("PRODUCE", True),
    "peach": ("PRODUCE", True),
    "peaches": ("PRODUCE", True),
    "pear": ("PRODUCE", True),
    "pears": ("PRODUCE", True),
    "nectarine": ("PRODUCE", True),
    "nectarines": ("PRODUCE", True),
    "apple": ("PRODUCE", True),
    "apples": ("PRODUCE", True),
    "bell pepper": ("PRODUCE", True),
    "hot pepper": ("PRODUCE", True),
    "jalapeno": ("PRODUCE", True),
    "cherry": ("PRODUCE", True),
    "cherries": ("PRODUCE", True),
    "blueberry": ("PRODUCE", True),
    "blueberries": ("PRODUCE", True),
    "green bean": ("PRODUCE", True),
    "green beans": ("PRODUCE", True),
    "tomato": ("PRODUCE", True),
    "tomatoes": ("PRODUCE", True),

    # CONDIMENTS & SWEETENERS
    "hot honey": ("PANTRY", False),
    "honey": ("PANTRY", False),

    # DAIRY
    "pepper jack cheese": ("DAIRY", False),
    "pepper jack": ("DAIRY", False),
    "butter": ("DAIRY", False),
    "milk": ("DAIRY", False),
    "heavy cream": ("DAIRY", False),
    "sour cream": ("DAIRY", False),
    "yogurt": ("DAIRY", False),
    "cheese": ("DAIRY", False),
    "parmesan": ("DAIRY", False),
    "cheddar": ("DAIRY", False),
    "mozzarella": ("DAIRY", False),
    "ricotta": ("DAIRY", False),
    "feta": ("DAIRY", False),
    "egg": ("DAIRY", False),
    "eggs": ("DAIRY", False),

    # MEAT & SEAFOOD
    "beef": ("MEAT", False),
    "ground beef": ("MEAT", False),
    "steak": ("MEAT", False),
    "chicken": ("MEAT", False),
    "chicken breast": ("MEAT", False),
    "chicken thighs": ("MEAT", False),
    "pork": ("MEAT", False),
    "bacon": ("MEAT", False),
    "sausage": ("MEAT", False),
    "salmon": ("MEAT", False),
    "fish": ("MEAT", False),
    "shrimp": ("MEAT", False),
    "tuna": ("MEAT", False),

    # PANTRY
    "olive oil": ("PANTRY", False),
    "extra-virgin olive oil": ("PANTRY", False),
    "vegetable oil": ("PANTRY", False),
    "canola oil": ("PANTRY", False),
    "sesame oil": ("PANTRY", False),
    "soy sauce": ("PANTRY", False),
    "tamari": ("PANTRY", False),
    "black pepper": ("PANTRY", False),
    "salt": ("PANTRY", False),
    "kosher salt": ("PANTRY", False),
    "sea salt": ("PANTRY", False),
    "sugar": ("PANTRY", False),
    "brown sugar": ("PANTRY", False),
    "flour": ("PANTRY", False),
    "all-purpose flour": ("PANTRY", False),
    "baking powder": ("PANTRY", False),
    "baking soda": ("PANTRY", False),
    "vanilla extract": ("PANTRY", False),
    "chicken broth": ("PANTRY", False),
    "vegetable broth": ("PANTRY", False),
    "beef broth": ("PANTRY", False),
    "pasta": ("PANTRY", False),
    "rice": ("PANTRY", False),
    "dried oregano": ("PANTRY", False),
    "ground cumin": ("PANTRY", False),
    "paprika": ("PANTRY", False),
    "smoked paprika": ("PANTRY", False),
    "cayenne pepper": ("PANTRY", False),
    "chili powder": ("PANTRY", False),
    "cinnamon": ("PANTRY", False),
    "nutmeg": ("PANTRY", False),
    "bay leaves": ("PANTRY", False),
    "bay leaf": ("PANTRY", False),
}

PANTRY_OVERRIDE_KEYWORDS = [
    "powder",
    "dried",
    "ground",
    "extract",
    "flakes",
    "seed",
    "seeds",
    "sauce",
    "paste",
    "vinegar",
    "seasoning",
    "broth",
    "stock",
    "oil",
    "canned",
]


def normalize_canonical_product_name(canonical_name: str, raw_text: str = "") -> str:
    """Standardizes canonical product names and handles substitutions."""
    name = (canonical_name or "").strip().lower()
    raw = (raw_text or "").strip().lower()

    if "lemon zest" in name or "lemon peel" in name or "lemon zest" in raw or "lemon peel" in raw:
        return "organic lemon"

    return name


def resolve_canonical_category(
    name: str,
    raw_text: Optional[str] = None,
    vlm_category: Optional[str] = None,
    vlm_dirty_dozen: Optional[bool] = None,
) -> Tuple[str, bool]:
    """Resolves category and dirty dozen status using catalog rules."""
    clean_name = (name or "").strip().lower()
    clean_raw = (raw_text or "").strip().lower()

    # 1. Exact catalog match
    if clean_name in CANONICAL_SEED_CATALOG:
        return CANONICAL_SEED_CATALOG[clean_name]

    # 2. Partial / Word-boundary catalog match (longest matching phrase wins)
    matching_keys = []
    for k in CANONICAL_SEED_CATALOG:
        pattern = rf"\b{re.escape(k)}\b"
        if re.search(pattern, clean_name) or re.search(pattern, clean_raw):
            matching_keys.append(k)

    if matching_keys:
        best_match = max(matching_keys, key=len)
        return CANONICAL_SEED_CATALOG[best_match]

    # 3. Spice & Pantry Keyword Overrides (Prevents "smoked paprika" -> MEAT)
    dairy_meat_guards = {"cheese", "milk", "cream", "beef", "chicken", "pork", "fish", "steak"}
    has_guard = any(re.search(rf"\b{re.escape(g)}\b", clean_name) for g in dairy_meat_guards)

    if not has_guard and any(
        re.search(rf"\b{re.escape(kw)}\b", clean_name) or re.search(rf"\b{re.escape(kw)}\b", clean_raw)
        for kw in PANTRY_OVERRIDE_KEYWORDS
    ):
        return "PANTRY", False

    # 4. Fallback to VLM suggestions or defaults
    cat = (vlm_category or "GENERAL").upper().strip()
    is_dirty = bool(vlm_dirty_dozen)
    return cat, is_dirty
