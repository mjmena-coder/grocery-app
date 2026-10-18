from typing import List, Optional, Dict, Any, Union
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from backend.models import CanonicalIngredient, Ingredient
from backend.services.vlm_service import ParsedIngredientSchema
from backend.services.canonical_catalog import resolve_canonical_category, normalize_canonical_product_name


def resolve_or_create_canonical_ingredient(session: Session, ingredient: Optional[ParsedIngredientSchema]) -> Optional[int]:
    """
    Attempts to match a parsed ingredient's canon name against existing
    CanonicalIngredient records. If none is found, auto-creates a new one.
    """
    raw_canonical_name = ingredient.canonical_name
    if not raw_canonical_name:
        return None

    # Map product-specific transforms (e.g. lemon zest -> organic lemon)
    canonical_name = normalize_canonical_product_name(raw_canonical_name, ingredient.raw_text or "")

    category, is_dirty = resolve_canonical_category(
            name=canonical_name,
            raw_text=ingredient.raw_text,
            vlm_category=ingredient.category,
            vlm_dirty_dozen=ingredient.is_dirty_dozen,
        )

    # If canonical_name is organic lemon, enforce dirty_dozen / organic consideration
    if canonical_name == "organic lemon":
        is_dirty = True

    # Exact case-insensitive match
    stmt = select(CanonicalIngredient.id).where(
        func.lower(CanonicalIngredient.name) == canonical_name.lower())
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
