from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_session
from backend.services.canonical_service import (
    get_unlinked_ingredients,
    merge_canonical_records
)

router = APIRouter(prefix="/canonical-ingredients", tags=["Canonical Ingredients"])


class CanonicalCreateSchema(BaseModel):
    name: str
    category: Optional[str] = None
    dirty_dozen: bool = False
    default_store_id: Optional[int] = None


class CanonicalUpdateSchema(BaseModel):
    category: Optional[str] = None
    dirty_dozen: Optional[bool] = None
    default_store_id: Optional[int] = None


class CanonicalMergeSchema(BaseModel):
    source_id: int
    target_id: int


@router.get("/")
def list_canonical_ingredients(
    category: Optional[str] = None,
    dirty_dozen: Optional[bool] = None,
    session: Session = Depends(get_session)
):
    """List master canonical ingredients, filterable by category or dirty dozen status."""
    return {"status": "ok", "canonical_ingredients": []}


@router.post("/")
def create_canonical_ingredient(
    payload: CanonicalCreateSchema,
    session: Session = Depends(get_session)
):
    """Manually add a new entry to the canonical ingredients dictionary."""
    return {"status": "created", "name": payload.name}


@router.get("/unlinked")
def list_unlinked_ingredients(session: Session = Depends(get_session)):
    """Fetch all recipe ingredients currently lacking a canonical_ingredient_id link."""
    return get_unlinked_ingredients(session)


@router.patch("/{canonical_id}")
def update_canonical_preferences(
    canonical_id: int,
    payload: CanonicalUpdateSchema,
    session: Session = Depends(get_session)
):
    """Update global settings for an ingredient (category, dirty dozen flag, default store)."""
    return {"status": "updated", "canonical_id": canonical_id}


@router.post("/merge")
def merge_ingredients(
    payload: CanonicalMergeSchema,
    session: Session = Depends(get_session)
):
    """Merge duplicate canonical entries and update ingredient foreign keys."""
    merge_canonical_records(session, payload.source_id, payload.target_id)
    return {"status": "merged", "source_id": payload.source_id, "target_id": payload.target_id}