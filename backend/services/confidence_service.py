from backend.services.vlm_service import VLMRecipeSchema

SEASONING_EXEMPTIONS = ["salt", "pepper", "oil for greasing", "garnish"]


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
        raw_text = ing.raw_text
        raw_lower = raw_text.lower()

        has_quantity = ing.quantity is not None
        is_seasoning = any(s in raw_lower for s in SEASONING_EXEMPTIONS)

        if not has_quantity and not is_seasoning:
            unquantified.append(raw_text)

    if unquantified:
        score -= 0.1 * len(unquantified)
        reasons.append(
            f"{len(unquantified)} ingredient(s) missing an obvious quantity: {unquantified}"
        )

    return max(0.0, round(score, 2)), reasons