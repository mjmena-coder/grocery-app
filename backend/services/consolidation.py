# backend/services/consolidation.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models import Ingredient, Recipe as RecipeRow
from backend.consolidation_engine import consolidate_ingredients, IngredientInput
from backend.services.store_router import StoreRouter

def build_consolidated_list(
    session: Session, 
    recipe_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Fetches raw ingredients, runs consolidation, flattens fields into clean strings,
    and assigns target stores.
    """
    stmt = select(Ingredient)
    if recipe_ids:
        stmt = stmt.where(Ingredient.recipe_id.in_(recipe_ids))
    
    raw_ingredients = session.scalars(stmt).all()
    if not raw_ingredients:
        return []

    input_list = [
        IngredientInput(
            id=ing.id,
            raw_name=ing.raw_name,
            quantity=ing.quantity,
            unit=ing.unit,
            needs_manual_review=ing.needs_manual_review,
            review_reason=ing.review_reason,
        )
        for ing in raw_ingredients
    ]

    consolidated = consolidate_ingredients(input_list)

    recipes = session.scalars(select(RecipeRow)).all()
    recipe_map = {r.id: r.title for r in recipes}
    ing_to_recipe = {
        ing.id: recipe_map.get(ing.recipe_id, "Unknown Recipe") 
        for ing in raw_ingredients
    }

    output = []
    for idx, item in enumerate(consolidated):
        # Safely extract values whether item is a dict or an object
        if isinstance(item, dict):
            name = item.get("canonical_name") or item.get("raw_name") or "Unknown Item"
            qty = item.get("quantity")
            unit = item.get("unit") or ""
            cat = item.get("category") or "pantry"
            source_ids = item.get("source_ingredient_ids", [idx + 1])
        else:
            name = getattr(item, "canonical_name", None) or getattr(item, "raw_name", None) or "Unknown Item"
            qty = getattr(item, "quantity", None)
            unit = getattr(item, "unit", "") or ""
            cat = getattr(item, "category", "pantry") or "pantry"
            source_ids = getattr(item, "source_ingredient_ids", [idx + 1])

        assigned_store = StoreRouter.assign_store(str(name), str(cat))

        recipe_titles = list({ing_to_recipe.get(sid) for sid in source_ids if sid in ing_to_recipe})

        # Format quantity cleanly as a readable string
        if qty is not None:
            qty_str = f"{qty} {unit}".strip()
        else:
            qty_str = unit.strip() if unit else None

        output.append({
            "id": idx + 1,
            "canonical_name": str(name).strip(),
            "quantity_display": qty_str,
            "category": str(cat).upper().strip(),
            "assigned_store": str(assigned_store).strip(),
            "recipes": recipe_titles
        })

    return output