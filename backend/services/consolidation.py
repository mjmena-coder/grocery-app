from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from backend.models import Ingredient, Recipe as RecipeRow, CanonicalIngredient, Store
from backend.consolidation_engine import consolidate_ingredients
from backend.services.store_router import StoreRouter

def build_consolidated_list(
    session: Session, 
    recipe_ids: Optional[List[int]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches raw ingredients with their canonical links, runs consolidation,
    respects database-driven store defaults and categories, and attaches provenance.
    Returns both consolidated items and kitchen staples.
    """
    stmt = select(Ingredient).options(
        selectinload(Ingredient.canonical_ingredient).selectinload(CanonicalIngredient.default_store)
    )
    if recipe_ids:
        stmt = stmt.where(Ingredient.recipe_id.in_(recipe_ids))
    
    raw_ingredients = session.scalars(stmt).all()

    if not raw_ingredients:
        return {"items": [], "kitchen_staples": []}

    raw_ingredients_canonical = []
    raw_ingredients_staples = []
    
    for ingredient in raw_ingredients:
        if getattr(ingredient, "canonical_ingredient", None):
            raw_ingredients_canonical.append(ingredient)
        else:
            raw_ingredients_staples.append(ingredient)

    consolidated_canonical = consolidate_ingredients(raw_ingredients_canonical)
    consolidated_kitchen_staples = consolidate_ingredients(raw_ingredients_staples)

    recipes = session.scalars(select(RecipeRow)).all()
    recipe_map = {r.id: r.title for r in recipes}
    
    # Map ingestion IDs to canonical metadata and recipes
    ing_meta_map = {}
    for ing in raw_ingredients:
        recipe_title = recipe_map.get(ing.recipe_id, "Unknown Recipe")
        canon = ing.canonical_ingredient
        
        category = "GENERAL"
        if canon and canon.category:
            category = canon.category

        assigned_store = None
        if canon and canon.default_store:
            assigned_store = canon.default_store.name
        else:
            name_val = canon.name if canon and canon.name else ing.raw_name
            assigned_store = StoreRouter.assign_store(name_val, category)

        ing_meta_map[ing.id] = {
            "recipe_title": recipe_title,
            "dirty_dozen": canon.dirty_dozen if canon else False,
            "organic_considerations": canon.organic_considerations if canon else [],
            "assigned_store": assigned_store,
            "category": category,
            "size_descriptor": ing.size_descriptor,
            "comment": ing.comment
        }

    # --- Helper logic to format item dictionaries cleanly ---
    def format_output_items(consolidated_batch, is_staple=False):
        formatted_output = []
        for idx, item in enumerate(consolidated_batch):
            name = item.get("name") or item.get("raw_name") or "Unknown Item"
            source_ids = item.get("source_ingredient_ids", [idx + 1])

            recipe_titles = set()
            is_dirty_dozen = False
            organic_notes = []
            assigned_store = StoreRouter.assign_store(str(name), "GENERAL")
            category = "GENERAL"
            prep_notes = set()

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
                    if meta.get("comment"):
                        prep_notes.add(meta["comment"].strip())

            qty_str = item.get("quantity_display") or item.get("display_text")
            if not qty_str:
                qty_val = item.get("quantity")
                unit_val = item.get("unit") or ""
                if qty_val is not None:
                    clean_qty = int(qty_val) if isinstance(qty_val, float) and qty_val.is_integer() else qty_val
                    qty_str = f"{clean_qty} {unit_val}".strip()
                elif unit_val:
                    qty_str = unit_val.strip()

            formatted_output.append({
                "id": idx + 1,
                "canonical_name": str(name).strip(),
                "quantity_display": qty_str,
                "original_quantity_display": item.get("original_display_text") or qty_str,
                "prep_notes": list(prep_notes),
                "category": str(category).upper().strip(),
                "assigned_store": str(assigned_store).strip(),
                "recipes": list(recipe_titles),
                "dirty_dozen": is_dirty_dozen,
                "organic_considerations": list(set(organic_notes))
            })
        return formatted_output

    return {
        "items": format_output_items(consolidated_canonical),
        "kitchen_staples": format_output_items(consolidated_kitchen_staples)
    }
