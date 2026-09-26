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