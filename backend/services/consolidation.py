from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from backend.models import Ingredient, Recipe as RecipeRow, CanonicalIngredient, Store
from backend.consolidation_engine import consolidate_ingredients, IngredientInput
from backend.services.store_router import StoreRouter

def build_consolidated_list(
    session: Session, 
    recipe_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Fetches raw ingredients with their canonical links, runs consolidation,
    respects database-driven store defaults and categories, and attaches provenance.
    """
    # Eager-load canonical ingredient and its default store relationship
    stmt = select(Ingredient).options(
        selectinload(Ingredient.canonical_ingredient).selectinload(CanonicalIngredient.default_store)
    )
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
    
    # Map ingestion IDs to canonical metadata and recipes
    ing_meta_map = {}
    for ing in raw_ingredients:
        recipe_title = recipe_map.get(ing.recipe_id, "Unknown Recipe")
        
        canon = ing.canonical_ingredient
        is_dirty = canon.dirty_dozen if canon else False
        org_considerations = canon.organic_considerations if canon else []
        
        # [UPDATED: Read category directly from database CanonicalIngredient, defaulting to GENERAL instead of pantry]
        category = "GENERAL"
        if canon and canon.category:
            category = canon.category

        # Determine store: Database default store takes precedence over StoreRouter fallback
        assigned_store = None
        if canon and canon.default_store:
            assigned_store = canon.default_store.name
        else:
            name_val = canon.name if canon and canon.name else ing.raw_name
            assigned_store = StoreRouter.assign_store(name_val, category)

        ing_meta_map[ing.id] = {
            "recipe_title": recipe_title,
            "dirty_dozen": is_dirty,
            "organic_considerations": org_considerations,
            "assigned_store": assigned_store,
            "category": category
        }

    output = []
    for idx, item in enumerate(consolidated):
        # [UPDATED: Removed defensive isinstance/getattr hedging. 
        # consolidation_engine strictly returns uniform dictionaries.]
        name = item.get("canonical_name") or item.get("raw_name") or "Unknown Item"
        qty = item.get("quantity")
        unit = item.get("unit") or ""
        source_ids = item.get("source_ingredient_ids", [idx + 1])

        # Aggregate recipe titles and flags across consolidated source items
        recipe_titles = set()
        is_dirty_dozen = False
        organic_notes = []
        assigned_store = StoreRouter.assign_store(str(name), "GENERAL")
        category = "GENERAL"

        for sid in source_ids:
            if sid in ing_meta_map:
                meta = ing_meta_map[sid]
                recipe_titles.add(meta["recipe_title"])
                if meta["dirty_dozen"]:
                    is_dirty_dozen = True
                if meta["organic_considerations"]:
                    organic_notes.extend(meta["organic_considerations"])
                if meta["assigned_store"]:
                    assigned_store = meta["assigned_store"]
                if meta["category"]:
                    category = meta["category"]

        if qty is not None:
            qty_str = f"{qty} {unit}".strip()
        else:
            qty_str = unit.strip() if unit else None

        output.append({
            "id": idx + 1,
            "canonical_name": str(name).strip(),
            "quantity_display": qty_str,
            "category": str(category).upper().strip(),
            "assigned_store": str(assigned_store).strip(),
            "recipes": list(recipe_titles),
            "dirty_dozen": is_dirty_dozen,
            "organic_considerations": list(set(organic_notes))
        })

    return output