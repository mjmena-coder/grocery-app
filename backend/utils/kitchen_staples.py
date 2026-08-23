import re

# TODO: Add CRUD functionality to this regex.
KITCHEN_STAPLE_INGREDIENTS = re.compile(
    r"\b(sugar|salt|pepper|oil|water?)\b"
)