# backend/services/consolidation.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.models import Ingredient, Recipe as RecipeRow
# Assuming consolidate_ingredients & IngredientInput live in your engine/library:
from backend.consolidation_engine import consolidate_ingredients, IngredientInput
from backend.services.store_router import StoreRouter

def build_consolidated_list(
    session: Session, 
    recipe_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Fetches raw ingredients, runs consolidation, attaches recipe provenance,
    and assigns target stores.
    """
    query = session.query(Ingredient)
    if recipe_ids:
        query = query.filter(Ingredient.recipe_id.in_(recipe_ids))
    
    raw_ingredients = query.all()
    if not raw_ingredients:
        return []

    # Map database rows to consolidation engine inputs
    input_list = [
        IngredientInput(
            id=ing.id,
            raw_name=ing.raw_name,
            quantity=ing.quantity,
            unit=ing.unit,
            needs_manual_review=getattr(ing, "needs_manual_review", False),
            review_reason=getattr(ing, "review_reason", None),
        )
        for ing in raw_ingredients
    ]

    consolidated = consolidate_ingredients(input_list)

    # Build recipe lookup table for provenance
    recipes = session.query(RecipeRow).all()
    recipe_map = {r.id: r.title for r in recipes}
    ing_to_recipe = {
        ing.id: recipe_map.get(ing.recipe_id, "Unknown Recipe") 
        for ing in raw_ingredients
    }

    output = []
    for idx, item in enumerate(consolidated):
        item_id = getattr(item, "id", idx + 1)
        name = getattr(item, "canonical_name", None) or getattr(item, "raw_name", None) or str(item)
        qty = getattr(item, "quantity", None)
        unit = getattr(item, "unit", "") or ""
        cat = getattr(item, "category", "pantry") or "pantry"

        # Resolve store mapping using the StoreRouter service
        assigned_store = StoreRouter.assign_store(name, cat)

        # Resolve recipe provenance
        source_ids = getattr(item, "source_ingredient_ids", [item_id])
        recipe_titles = list({ing_to_recipe.get(sid) for sid in source_ids if sid in ing_to_recipe})

        qty_str = f"{qty} {unit}".strip() if qty is not None else None

        output.append({
            "id": item_id,
            "canonical_name": name,
            "quantity_display": qty_str,
            "category": cat,
            "assigned_store": assigned_store,
            "recipes": recipe_titles
        })

    return output