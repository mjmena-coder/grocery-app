from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models import GroceryItem, Store, CanonicalIngredient
from backend.utils.units import adjust_unit_plurality

def save_generated_list(session: Session, consolidated_items: List[Dict[str, Any]], kitchen_staples: List[Dict[str, Any]]) -> None:
    """Deactivates old active items and persists newly generated grocery items and kitchen staples."""
    existing_active = session.scalars(
        select(GroceryItem).where(GroceryItem.is_active == True)
    ).all()
    
    for old_item in existing_active:
        old_item.is_active = False
        session.add(old_item)

    for item in consolidated_items:
        session.add(GroceryItem(
            canonical_name=item["canonical_name"],
            quantity_display=item.get("quantity_display"),
            original_quantity_display=item.get("original_quantity_display") or item.get("quantity_display"),
            category=item["category"],
            assigned_store=item["assigned_store"],
            recipes=item["recipes"],
            is_active=True,
            is_checked=False
        ))

    for item in kitchen_staples:
        session.add(GroceryItem(
            canonical_name=item["canonical_name"],
            quantity_display=item.get("quantity_display"),
            original_quantity_display=item.get("original_quantity_display") or item.get("quantity_display"),
            category=item["category"],
            assigned_store=item["assigned_store"],
            recipes=item["recipes"],
            is_active=True,
            is_checked=False,
            is_kitchen_staple=True
        ))
    session.commit()

def fetch_current_list_grouped(session: Session) -> Dict[str, Any]:
    """Fetches and groups active grocery items by store, kitchen staples, and deleted items."""
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
        "items": grouped_items,
        "kitchen_staples": kitchen_staples,
        "deleted_items": deleted_items
    }

def update_grocery_item_record(session: Session, item_id: int, payload: Any) -> GroceryItem:
    """Updates store assignment, quantity display with plurality adjustment, or soft deletion."""
    item = session.get(GroceryItem, item_id)
    if not item:
        return None

    if payload.assigned_store is not None:
        item.assigned_store_override = payload.assigned_store
        if payload.save_as_default:
            store = session.scalars(select(Store).where(Store.name == payload.assigned_store)).first()
            if store:
                canonical = session.scalars(select(CanonicalIngredient).where(CanonicalIngredient.name == item.canonical_name)).first()
                if canonical:
                    canonical.default_store_id = store.id
                    session.add(canonical)

    if payload.quantity_display is not None:
        adjusted = adjust_unit_plurality(payload.quantity_display)
        if item.original_quantity_display is None:
            item.original_quantity_display = item.quantity_display
        item.quantity_display = adjusted

    if payload.is_deleted is not None:
        item.is_deleted = payload.is_deleted
        item.deleted_at = datetime.utcnow() if payload.is_deleted else None

    session.add(item)
    session.commit()
    session.refresh(item)
    return item
