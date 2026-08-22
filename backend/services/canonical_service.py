from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from backend.models import CanonicalIngredient, Ingredient
from backend.services.vlm_service import ParsedIngredientSchema
from backend.services.canonical_catalog import resolve_canonical_category, CANONICAL_SEED_CATALOG


def resolve_or_create_canonical_ingredient(session: Session, raw_name: Optional[str]) -> Optional[int]:
    """
    Attempts to match a parsed ingredient's raw_name against existing 
    CanonicalIngredient records. If none is found, auto-creates a new one.
    """
    if not raw_name:
        return None

    cleaned_name = raw_name.strip().lower()

    # Step 1: Exact match (case-insensitive)
    stmt = select(CanonicalIngredient.id).where(
        func.lower(CanonicalIngredient.name) == cleaned_name
    )
    canonical_id = session.scalar(stmt)
    if canonical_id:
        return canonical_id

    # Step 2a: Raw input contains Canonical name
    stmt_raw_contains = select(CanonicalIngredient.id).where(
        func.instr(cleaned_name, func.lower(CanonicalIngredient.name)) > 0
    )
    canonical_id = session.scalar(stmt_raw_contains)
    if canonical_id:
        return canonical_id

    # Step 2b: Canonical name contains Raw input
    stmt_canonical_contains = select(CanonicalIngredient.id).where(
        func.lower(CanonicalIngredient.name).like(f"%{cleaned_name}%")
    )
    canonical_id = session.scalar(stmt_canonical_contains)
    if canonical_id:
        return canonical_id

    # 🚀 Step 3: AUTO-SEED / CREATE IF MISSING
    new_canonical = CanonicalIngredient(
        name=cleaned_name,
        category="General",  # Default category or pass through if available
        dirty_dozen=False
    )
    session.add(new_canonical)
    session.flush()  # Flushes to database immediately so new_canonical.id is generated
    
    return new_canonical.id


def resolve_or_create_canonical_ingredient(session: Session, ingredient: Optional[ParsedIngredientSchema]) -> Optional[int]:
    """
    Attempts to match a parsed ingredient's canon name against existing 
    CanonicalIngredient records. If none is found, auto-creates a new one.
    """
    canonical_name = ingredient.canonical_name
    if not canonical_name:
        return None

    category, is_dirty = resolve_canonical_category(
            name=ingredient.canonical_name, # Using canonical name instead of cleaned_name, expect already cleaned.
            raw_text=ingredient.raw_text,
            vlm_category=ingredient.category,
            vlm_dirty_dozen=ingredient.is_dirty_dozen,
        )

    # Compare directly to names in CanonicalIngredients.
    stmt = select(CanonicalIngredient.id).where(
        func.lower(CanonicalIngredient.name) == canonical_name
    )
    canonical_id = session.scalar(stmt)
    if canonical_id:
        return canonical_id

    # Create because match not found.
    new_canonical = CanonicalIngredient(
        name=canonical_name,
        category=category,
        dirty_dozen=is_dirty,
        organic_considerations=ingredient.organic_considerations
        # Missing default store id may be needed, may not...
    )
    session.add(new_canonical)
    session.flush()  # Flushes to database immediately so new_canonical.id is generated
    
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