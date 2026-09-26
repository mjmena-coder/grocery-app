import re

# TODO: Add CRUD functionality to this regex.
KITCHEN_STAPLE_INGREDIENTS = re.compile(
    r"\b("
    r"sugar|salt|kosher salt|sea salt|black pepper|white pepper|table salt|"
    r"oil|olive oil|vegetable oil|canola oil|cooking spray|"
    r"water|tap water|ice water|"
    r"garlic powder|onion powder|baking powder|baking soda|flour|all-purpose flour|"
    r"dried oregano|dried basil|dried thyme|dried rosemary|dried parsley|"
    r"paprika|smoked paprika|cayenne pepper|chili powder|ground cumin|cinnamon|ground cinnamon"
    r")\b",
    re.IGNORECASE,
)
