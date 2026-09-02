from typing import List, Optional, Dict, Any, Union
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from backend.models import CanonicalIngredient, Ingredient
from backend.services.vlm_service import ParsedIngredientSchema
from backend.services.canonical_catalog import resolve_canonical_category


def resolve_or_create_canonical_ingredient(
    session: Session, 
    ingredient: Union[str, ParsedIngredientSchema, None]
) -> Optional[int]:
    """
    Attempts to match a parsed ingredient or raw string against existing 
    CanonicalIngredient records. If none is found, auto-creates a new one.
    """
    if ingredient is None:
        return None

    if isinstance(ingredient, str):
        canonical_name = ingredient.strip()
        raw_text = ingredient
        vlm_category = None
        is_dirty = False
        organic_considerations = None
    else:
        canonical_name = (ingredient.canonical_name or ingredient.raw_text or "").strip()
        raw_text = ingredient.raw_text
        vlm_category = ingredient.category
        is_dirty = ingredient.is_dirty_dozen
        organic_considerations = ingredient.organic_considerations

    if not canonical_name:
        return None

    cleaned_lower = canonical_name.lower()

    # Step 1: Exact match (case-insensitive)
    stmt = select(CanonicalIngredient.id).where(
        func.lower(CanonicalIngredient.name) == cleaned_lower
    )
    canonical_id = session.scalar(stmt)
    if canonical_id:
        return canonical_id

    # Step 2a: Raw/Canonical input contains existing Canonical name
    stmt_raw_contains = select(CanonicalIngredient.id).where(
        func.instr(cleaned_lower, func.lower(CanonicalIngredient.name)) > 0
    )
    canonical_id = session.scalar(stmt_raw_contains)
    if canonical_id:
        return canonical_id

    # Step 2b: Existing Canonical name contains input
    stmt_canonical_contains = select(CanonicalIngredient.id).where(
        func.lower(CanonicalIngredient.name).like(f"%{cleaned_lower}%")
    )
    canonical_id = session.scalar(stmt_canonical_contains)
    if canonical_id:
        return canonical_id

    # Step 3: Resolve category & dirty dozen classification
    category, dirty_dozen_flag = resolve_canonical_category(
        name=canonical_name,
        raw_text=raw_text,
        vlm_category=vlm_category,
        vlm_dirty_dozen=is_dirty,
    )

    # Step 4: Create new record
    new_canonical = CanonicalIngredient(
        name=canonical_name,
        category=category,
        dirty_dozen=dirty_dozen_flag,
        organic_considerations=organic_considerations,
    )
    session.add(new_canonical)
    session.flush()
    
    return new_canonical.id


def get_unlinked_ingredients(session: Session) -> List[Dict[str, Any]]:
    """
    Fetches all recipe ingredient records that currently do not have a 
    canonical_ingredient_id assigned.
    """
    stmt = select(Ingredient).where(Ingredient.canonical_ingredient_id.is_(None))
    unlinked_rows = session.scalars(stmt).all()

    return [
        {
            "ingredient_id": ing.id,
            "recipe_id": ing.recipe_id,
            "raw_name": ing.raw_name,
            "review_reason": ing.review_reason,
        }
        for ing in unlinked_rows
    ]


def merge_canonical_records(session: Session, source_id: int, target_id: int) -> None:
    """
    Re-assigns all Ingredient records pointing to source_id to target_id,
    then deletes the redundant source CanonicalIngredient record.
    """
    # 1. Verify target exists
    target = session.get(CanonicalIngredient, target_id)
    if not target:
        raise ValueError(f"Target CanonicalIngredient with id={target_id} does not exist.")

    # 2. Update foreign keys on all matching ingredients
    session.execute(
        update(Ingredient)
        .where(Ingredient.canonical_ingredient_id == source_id)
        .values(canonical_ingredient_id=target_id)
    )

    # 3. Delete source canonical record
    source = session.get(CanonicalIngredient, source_id)
    if source:
        session.delete(source)

    session.commit()
