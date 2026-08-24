from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from backend.models import Ingredient, Recipe as RecipeRow, CanonicalIngredient, Store
from backend.consolidation_engine import consolidate_ingredients
from backend.services.store_router import StoreRouter

def build_consolidated_list(
    session: Session, 
    recipe_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Fetches raw ingredients with their canonical links, runs consolidation,
    respects database-driven store defaults and categories, and attaches provenance.
    """
    # Eager-load canonical ingredient (if it exists) and its default store relationship
    # Currently, canonical service does not take into account store, which is a db object that isn't implemented...
    stmt = select(Ingredient).options(
        selectinload(Ingredient.canonical_ingredient).selectinload(CanonicalIngredient.default_store)
    )
    if recipe_ids:
        stmt = stmt.where(Ingredient.recipe_id.in_(recipe_ids))
    # Fetch raw ingredients.
    raw_ingredients = session.scalars(stmt).all()

    if not raw_ingredients:
        return []

    raw_ingredients_canonical = []
    raw_ingredients_staples = []
    # Separate canonical and kitchen staples ingredients.
    for ingredient in raw_ingredients:
        if getattr(ingredient, "canonical_ingredient", None):
            raw_ingredients_canonical.append(ingredient)
        else:
            raw_ingredients_staples.append(ingredient)

    # parse them out seprately.
    # Consolidation engine that does all the ingredient addition and parsing.
    print("\n--- STAGE 3: FINAL Staples TO ROUTER ---")
    for item in raw_ingredients_staples:
        print(f"FINAL DTO -> raw_name: '{item.raw_name} | quantity: '{item.quantity}' ")
    consolidated_canonical = consolidate_ingredients(raw_ingredients_canonical)
    consolidated_kitchen_staples = consolidate_ingredients(raw_ingredients_staples)


    recipes = session.scalars(select(RecipeRow)).all()
    recipe_map = {r.id: r.title for r in recipes}
    
    # Map ingestion IDs to canonical metadata and recipes
    ing_meta_map = {}
    for ing in raw_ingredients:
        recipe_title = recipe_map.get(ing.recipe_id, "Unknown Recipe")
        
        canon = ing.canonical_ingredient
        is_dirty = canon.dirty_dozen if canon else False
        org_considerations = canon.organic_considerations if canon else []
        
        category = "GENERAL"
        if canon and canon.category:
            category = canon.category

        assigned_store = None
        # Currently, will always hit else bc no store setup in canonical service.
        if canon and canon.default_store:
            assigned_store = canon.default_store.name
        else:
            name_val = canon.name if canon and canon.name else ing.raw_name
            assigned_store = StoreRouter.assign_store(name_val, category) # Store router contains very generic ingredient separation but tries to use category for assignment. 

        # Metadata that maps the canonical stuff to the current ingredient being processed.
        ing_meta_map[ing.id] = {
            "recipe_title": recipe_title,
            "dirty_dozen": is_dirty,
            "organic_considerations": org_considerations,
            "assigned_store": assigned_store,
            "category": category,
            "size_descriptor": ing.size_descriptor,
            "comment": ing.comment
        }
    # Finalize output dict of ingredients to be displayed. Go through all ingredients once again.
    output = []
    for idx, item in enumerate(consolidated_canonical):
        # The final name will be the name if it exists (which it should), otherwise use the raw name parsed from VLM.
        name = item.get("name") or item.get("raw_name") or "Unknown Item"
        # Source ID attached to display which recipe the ingredient belongs to.
        source_ids = item.get("source_ingredient_ids", [idx + 1])

        recipe_titles = set()
        is_dirty_dozen = False
        organic_notes = []
        # A duplicate store router...
        assigned_store = StoreRouter.assign_store(str(name), "GENERAL")
        category = "GENERAL"
        size_desc = None

        prep_notes = set()
        # Aggregate metadata and extract size_descriptor across consolidated_canonical source items
        for sid in source_ids:
            # If there's canonical mapping related to this recipe ingredient (which they all will have).
            if sid in ing_meta_map:
                meta = ing_meta_map[sid]
                recipe_titles.add(meta["recipe_title"])
                if meta["dirty_dozen"]:
                    # A little weird, bc the ingredient should map to same canonical ingredient, so either always dirty dozen or never. But we do it each time anyway.
                    is_dirty_dozen = True
                if meta["organic_considerations"]:
                    organic_notes.extend(meta["organic_considerations"])
                if meta["assigned_store"]:
                    # Same situation as dirty dozen designation.
                    assigned_store = meta["assigned_store"]
                if meta["category"]:
                    category = meta["category"]
                if meta.get("size_descriptor") and not size_desc:
                    # This one is genuinely problematic, because this means the last recipe will determine the size descriptor of a canonical ingredient.
                    # TODO: Probably test out to see if this plays out as expected.
                    size_desc = meta["size_descriptor"]
                if meta.get("comment"):
                    prep_notes.add(meta["comment"].strip())

        # 1. Grab pre-formatted string from engine or build fallback
        # There is no quantity_display at the moment coming from consolidation_engine list, so try quantity first otherwise use display_text (will have name of ingredient..)
        qty_str = item.get("quantity_display") or item.get("display_text")

        # Shouldn't be none....
        if not qty_str:
            qty_val = item.get("quantity")
            unit_val = item.get("unit") or ""
            
            if qty_val is not None:
                clean_qty = int(qty_val) if isinstance(qty_val, float) and qty_val.is_integer() else qty_val
                qty_str = f"{clean_qty} {unit_val}".strip()
            elif unit_val:
                qty_str = unit_val.strip()

        output.append({
            "id": idx + 1,
            "canonical_name": str(name).strip(),
            "quantity_display": qty_str, # This is the important value that is shown
            "prep_notes": list(prep_notes),
            "category": str(category).upper().strip(),
            "assigned_store": str(assigned_store).strip(),
            "recipes": list(recipe_titles),
            "dirty_dozen": is_dirty_dozen,
            "organic_considerations": list(set(organic_notes))
        })

    print("\n--- STAGE 3: FINAL DTO TO ROUTER ---")
    for item in output:
        print(f"FINAL DTO -> canonical_name: '{item['canonical_name']}' | quantity_display: '{item['quantity_display']}' | prep_notes: '{item['prep_notes']}'")
    print("\n--- STAGE 3: FINAL Staples TO ROUTER ---")
    for item in consolidated_kitchen_staples:
        print(f"FINAL DTO -> canonical_name: '{item['name']}' | quantity: '{item['quantity']}' | display_text: '{item['display_text']}'")
    return output