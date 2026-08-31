import re
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_session
from backend.services.consolidation import build_consolidated_list
from backend.models import GroceryItem, Store, CanonicalIngredient

router = APIRouter(prefix="/grocery-list", tags=["Grocery List"])


def adjust_unit_plurality(text: str) -> str:
    """Adjusts basic ingredient quantity units for singular vs plural matching leading numbers."""
    match = re.match(r"^(\d+(?:\.\d+)?)\s*(.*)$", text.strip())
    if not match:
        return text
    val_str, rest = match.groups()
    try:
        val = float(val_str)
    except ValueError:
        return text

    units_map = {
        "cup": "cups", "cups": "cups",
        "clove": "cloves", "cloves": "cloves",
        "tablespoon": "tablespoons", "tablespoons": "tablespoons", "tbsp": "tbsp",
        "teaspoon": "teaspoons", "teaspoons": "teaspoons", "tsp": "tsp",
        "ounce": "ounces", "ounces": "ounces", "oz": "oz",
        "pound": "pounds", "pounds": "pounds", "lb": "lbs", "lbs": "lbs",
        "gram": "grams", "grams": "grams", "g": "g",
        "kilogram": "kilograms", "kilograms": "kilograms", "kg": "kg",
        "can": "cans", "cans": "cans",
        "bunch": "bunches", "bunches": "bunches",
        "head": "heads", "heads": "heads",
        "slice": "slices", "slices": "slices",
        "pinch": "pinches", "pinches": "pinches",
        "dash": "dashes", "dashes": "dashes",
    }

    words = rest.split()
    if words:
        first_word = words[0].lower()
        if first_word in units_map:
            base_unit = units_map[first_word]
            # Strictly equal to 1 is singular (e.g. 1 cup).
            # Fractional/decimals non-equal to 1 (e.g. 0.5 cups) and > 1 are plural.
            if val == 1.0:
                if base_unit.endswith("es") and base_unit not in ("dashes", "pinches", "bunches"):
                    singular = base_unit[:-2]
                elif base_unit.endswith("s") and base_unit not in ("oz", "lbs"):
                    singular = base_unit[:-1]
                elif base_unit in ("bunches", "pinches", "dashes"):
                    singular = base_unit[:-2]
                else:
                    singular = base_unit
                words[0] = singular
            else:
                words[0] = base_unit
            return f"{val_str} {' '.join(words)}"

    return text


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

    # 1. Deactivate previous active grocery items
    existing_active = session.scalars(
        select(GroceryItem).where(GroceryItem.is_active == True)
    ).all()
    
    for old_item in existing_active:
        old_item.is_active = False
        session.add(old_item)

    # 2. Persist newly generated items
    for item in consolidated_items:
        db_item = GroceryItem(
            canonical_name=item["canonical_name"],
            quantity_display=item["quantity_display"],
            original_quantity_display=item["quantity_display"],
            category=item["category"],
            assigned_store=item["assigned_store"],
            recipes=item["recipes"],
            is_active=True,
            is_checked=False
        )
        session.add(db_item)

    # 3. Persist newly generated kitchen staples
    for item in kitchen_staples:
        db_item = GroceryItem(
            canonical_name=item["canonical_name"],
            quantity_display=item["quantity_display"],
            original_quantity_display=item["quantity_display"],
            category=item["category"],
            assigned_store=item["assigned_store"],
            recipes=item["recipes"],
            is_active=True,
            is_checked=False,
            is_kitchen_staple=True
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
    """Fetch active weekly grocery items grouped by store, kitchen staples, and deleted items history."""
    active_items = session.scalars(
        select(GroceryItem).where(GroceryItem.is_active == True)
    ).all()

    grouped_items = {}
    kitchen_staples = []
    deleted_items = []

    for item in active_items:
        item_data = {
            "id": item.id,
            "canonical_name": item.canonical_name,
            "quantity_display": item.quantity_display,
            "original_quantity_display": item.original_quantity_display,
            "category": item.category,
            "assigned_store": item.assigned_store_override or item.assigned_store,
            "recipes": item.recipes,
            "is_checked": item.is_checked,
            "is_kitchen_staple": item.is_kitchen_staple,
            "is_deleted": item.is_deleted,
            "deleted_at": item.deleted_at.isoformat() if item.deleted_at else None
        }

        if item.is_deleted:
            deleted_items.append(item_data)
        elif item.is_kitchen_staple and not item.assigned_store_override:
            kitchen_staples.append(item_data)
        else:
            store = item.assigned_store_override or item.assigned_store
            if store not in grouped_items:
                grouped_items[store] = []
            grouped_items[store].append(item_data)

    return {
        "status": "ok", 
        "items": grouped_items, 
        "kitchen_staples": kitchen_staples,
        "deleted_items": deleted_items
    }


@router.patch("/items/{item_id}")
def update_grocery_item(
    item_id: int,
    payload: UpdateListItemSchema,
    session: Session = Depends(get_session)
):
    """
    Updates store assignment (including moving staples individually), quantity display,
    or soft-deletion status.
    """
    item = session.get(GroceryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Grocery item not found")

    # 1. Store Assignment / Movement
    if payload.assigned_store is not None:
        item.assigned_store_override = payload.assigned_store
        
        if payload.save_as_default:
            store = session.scalars(
                select(Store).where(Store.name == payload.assigned_store)
            ).first()
            if store:
                canonical = session.scalars(
                    select(CanonicalIngredient).where(CanonicalIngredient.name == item.canonical_name)
                ).first()
                if canonical:
                    canonical.default_store_id = store.id
                    session.add(canonical)

    # 2. Quantity Display Update with Original History Preservation & Unit Plurality Adjustment
    if payload.quantity_display is not None:
        adjusted = adjust_unit_plurality(payload.quantity_display)
        if item.original_quantity_display is None:
            item.original_quantity_display = item.quantity_display
        item.quantity_display = adjusted

    # 3. Soft Delete Update
    if payload.is_deleted is not None:
        item.is_deleted = payload.is_deleted
        item.deleted_at = datetime.utcnow() if payload.is_deleted else None

    session.add(item)
    session.commit()
    session.refresh(item)

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


@router.post("/items/{item_id}/restore")
def restore_grocery_item(item_id: int, session: Session = Depends(get_session)):
    """Restores a soft-deleted grocery item for single-click UNDO actions."""
    item = session.get(GroceryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Grocery item not found")

    item.is_deleted = False
    item.deleted_at = None
    session.add(item)
    session.commit()

    return {"status": "restored", "item_id": item_id}


@router.post("/staples/move-all")
def bulk_move_staples(target_store: str, session: Session = Depends(get_session)):
    """Moves all active kitchen staples to a designated store."""
    staples = session.scalars(
        select(GroceryItem).where(
            GroceryItem.is_active == True,
            GroceryItem.is_kitchen_staple == True,
            GroceryItem.is_deleted == False
        )
    ).all()

    for staple in staples:
        staple.is_kitchen_staple = False
        staple.assigned_store_override = target_store
        session.add(staple)

    session.commit()
    return {"status": "ok", "moved_count": len(staples)}


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
