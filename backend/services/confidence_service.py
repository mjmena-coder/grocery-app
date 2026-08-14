from backend.services.vlm_service import VLMRecipeSchema

SEASONING_EXEMPTIONS = ["salt", "pepper", "oil for greasing", "garnish"]
FRACTION_CHARS = ["½", "¼", "¾", "⅓", "⅔"]


def calculate_extraction_confidence(recipe: VLMRecipeSchema) -> tuple[float, list[str]]:
    score = 1.0
    reasons = []

    if not recipe.ingredients:
        score -= 0.5
        reasons.append("no ingredients extracted")
    if not recipe.steps:
        score -= 0.3
        reasons.append("no steps extracted")

    unquantified = []
    for ing in recipe.ingredients:
        first_word = ing.strip().split()[0] if ing else ""
        has_digit = any(c.isdigit() for c in first_word) or any(f in first_word for f in FRACTION_CHARS)
        is_seasoning = any(s in ing.lower() for s in SEASONING_EXEMPTIONS)
        if not has_digit and not is_seasoning:
            unquantified.append(ing)

    if unquantified:
        score -= 0.1 * len(unquantified)
        reasons.append(f"{len(unquantified)} ingredient(s) missing an obvious quantity: {unquantified}")

    return max(0.0, round(score, 2)), reasons