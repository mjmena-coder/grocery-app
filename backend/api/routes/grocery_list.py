from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_session
from backend.services.consolidation import build_consolidated_list
from backend.services.grocery_service import (
    save_generated_list,
    fetch_current_list_grouped,
    update_grocery_item_record,
)
from backend.models import GroceryItem

router = APIRouter(prefix="/grocery-list", tags=["Grocery List"])


class GenerateListSchema(BaseModel):
    recipe_ids: List[int]


class UpdateListItemSchema(BaseModel):
    assigned_store: Optional[str] = None
    quantity_display: Optional[str] = None
    is_deleted: Optional[bool] = None
    save_as_default: bool = False


@router.post("/generate")
def generate_grocery_list(
    payload: GenerateListSchema,
    session: Session = Depends(get_session)
):
    """Consolidates ingredients across recipe_ids, persists them as active, and returns routed items."""
    result = build_consolidated_list(session, recipe_ids=payload.recipe_ids)
    consolidated_items = result.get("items", [])
    kitchen_staples = result.get("kitchen_staples", [])
    
    if not consolidated_items and not kitchen_staples:
        return {"status": "ok", "items": [], "kitchen_staples": []}

    save_generated_list(session, consolidated_items, kitchen_staples)

    return {
        "status": "ok", 
        "items": consolidated_items, 
        "kitchen_staples": kitchen_staples
    }


@router.get("/current")
def get_current_list(session: Session = Depends(get_session)):
    """Fetch active weekly grocery items grouped by store, kitchen staples, and deleted items history."""
    data = fetch_current_list_grouped(session)
    return {"status": "ok", **data}


@router.patch("/items/{item_id}")
def update_grocery_item(
    item_id: int,
    payload: UpdateListItemSchema,
    session: Session = Depends(get_session)
):
    """Updates store assignment, quantity display, or soft-deletion status."""
    item = update_grocery_item_record(session, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Grocery item not found")

    return {
        "status": "updated",
        "item_id": item_id,
        "assigned_store": item.assigned_store_override or item.assigned_store,
        "quantity_display": item.quantity_display,
        "original_quantity_display": item.original_quantity_display,
        "is_deleted": item.is_deleted
    }


@router.delete("/items/{item_id}")
def soft_delete_grocery_item(item_id: int, session: Session = Depends(get_session)):
    """Soft deletes a grocery item and sets deleted_at timestamp."""
    item = session.get(GroceryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Grocery item not found")

    item.is_deleted = True
    item.deleted_at = datetime.utcnow()
    session.add(item)
    session.commit()

    return {"status": "deleted", "item_id": item_id}


@router.patch("/items/{item_id}/toggle")
def toggle_grocery_item(item_id: int, session: Session = Depends(get_session)):
    """Toggle the checked state of an active grocery item."""
    item = session.get(GroceryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.is_checked = not item.is_checked
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return {"status": "ok", "is_checked": item.is_checked}


@router.delete("/current")
def clear_current_list(session: Session = Depends(get_session)):
    """Clear active weekly list."""
    existing_active = session.scalars(
        select(GroceryItem).where(GroceryItem.is_active == True)
    ).all()
    for item in existing_active:
        item.is_active = False
        session.add(item)
    session.commit()
    return {"status": "cleared"}
