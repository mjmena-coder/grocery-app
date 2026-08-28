from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_session
from backend.services.consolidation import build_consolidated_list
from backend.models import GroceryItem, Store, CanonicalIngredient

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
    """Consolidates ingredients across recipe_ids, persists them as active, and returns routed items."""
    result = build_consolidated_list(session, recipe_ids=payload.recipe_ids)
    consolidated_items = result.get("items", [])
    kitchen_staples = result.get("kitchen_staples", [])
    
    if not consolidated_items and not kitchen_staples:
        return {"status": "ok", "items": [], "kitchen_staples": []}

    # 1. Deactivate previous active grocery items
    existing_active = session.scalars(
        select(GroceryItem).where(GroceryItem.is_active == True)
    ).all()
    
    for old_item in existing_active:
        old_item.is_active = False
        session.add(old_item)

    # 2. Persist newly generated items (Optional: handle staples persistence here too if needed)
    for item in consolidated_items:
        db_item = GroceryItem(
            canonical_name=item["canonical_name"],
            quantity_display=item["quantity_display"],
            category=item["category"],
            assigned_store=item["assigned_store"],
            recipes=item["recipes"],
            is_active=True,
            is_checked=False
        )
        session.add(db_item)

    # 3. Persist newly generated kitchen staples (Setting is_kitchen_staple=True)
    for item in kitchen_staples:
        db_item = GroceryItem(
            canonical_name=item["canonical_name"],
            quantity_display=item["quantity_display"],
            category=item["category"],
            assigned_store=item["assigned_store"],
            recipes=item["recipes"],
            is_active=True,
            is_checked=False,
            is_kitchen_staple=True # Explicitly a staple.
        )
        session.add(db_item)


    session.commit()

    return {
        "status": "ok", 
        "items": consolidated_items, 
        "kitchen_staples": kitchen_staples
    }

@router.get("/current")
def get_current_list(session: Session = Depends(get_session)):
    """Fetch active weekly grocery items and kitchen staples."""
    active_items = session.scalars(
        select(GroceryItem).where(GroceryItem.is_active == True)
    ).all()

    grouped_items = {}
    kitchen_staples = []

    for item in active_items:
        item_data = {
            "id": item.id,
            "canonical_name": item.canonical_name,
            "quantity_display": item.quantity_display,
            "category": item.category,
            "assigned_store": item.assigned_store,
            "recipes": item.recipes,
            "is_checked": item.is_checked
        }

        # Check if the item is a kitchen staple
        if item.is_kitchen_staple:
            kitchen_staples.append(item_data)
        else:
            store = item.assigned_store
            if store not in grouped_items:
                grouped_items[store] = []
            grouped_items[store].append(item_data)

    return {
        "status": "ok", 
        "items": grouped_items, 
        "kitchen_staples": kitchen_staples
    }


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
    item = session.get(GroceryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Grocery item not found")
    
    # 1. Update the active grocery item's assigned store
    item.assigned_store = payload.assigned_store
    session.add(item)

    # 2. Optionally save as global default preference
    if payload.save_as_default:
        # Find the store record to get its ID
        store = session.scalars(
            select(Store).where(Store.name == payload.assigned_store)
        ).first()
        
        if store:
            # Find the matching canonical ingredient by name
            canonical = session.scalars(
                select(CanonicalIngredient).where(CanonicalIngredient.name == item.canonical_name)
            ).first()
            
            if canonical:
                canonical.default_store_id = store.id
                session.add(canonical)

    session.commit()
    session.refresh(item)

    return {
        "status": "updated",
        "item_id": item_id,
        "assigned_store": item.assigned_store,
        "saved_as_default": payload.save_as_default
    }


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
    return {"status": "cleared"}