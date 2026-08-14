from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_session
from backend.services.consolidation import build_consolidated_list

router = APIRouter(prefix="/grocery-list", tags=["Grocery List"])


class GenerateListSchema(BaseModel):
    recipe_ids: List[int]


class UpdateListItemSchema(BaseModel):
    assigned_store: str
    save_as_default: bool = False  # If True, updates CanonicalIngredient.default_store_id


@router.post("/generate")
def generate_grocery_list(
    payload: GenerateListSchema,
    session: Session = Depends(get_session)
):
    """Consolidates ingredients across recipe_ids and returns routed grocery items."""
    consolidated = build_consolidated_list(session, recipe_ids=payload.recipe_ids)
    return {"status": "ok", "items": consolidated}


@router.get("/current")
def get_current_list(session: Session = Depends(get_session)):
    """Fetch active weekly grocery items grouped by target store."""
    return {"status": "ok", "items": []}


@router.patch("/items/{item_id}")
def update_item_store(
    item_id: int,
    payload: UpdateListItemSchema,
    session: Session = Depends(get_session)
):
    """
    Updates assigned store for this week's list.
    Optionally sets save_as_default=True to persist choice as global preference.
    """
    return {
        "status": "updated",
        "item_id": item_id,
        "assigned_store": payload.assigned_store,
        "saved_as_default": payload.save_as_default
    }


@router.patch("/items/{item_id}/toggle")
def toggle_item_checked(item_id: int, session: Session = Depends(get_session)):
    """Toggle item checked/purchased status on active list."""
    return {"status": "toggled", "item_id": item_id}


@router.delete("/current")
def clear_current_list(session: Session = Depends(get_session)):
    """Clear active weekly list."""
    return {"status": "cleared"}