from unittest.mock import patch
import pytest
from sqlalchemy import select
from backend.models import GroceryItem, Store, CanonicalIngredient


def test_update_item_store_reassignment(client, session):
    """
    Asserts a grocery list item can be moved from one store to
another.
    When save_as_default is True, updates the CanonicalIngredient
default store preference.
    """
    store_a = Store(name="King Soopers")
    store_b = Store(name="Trader Joe's")
    session.add_all([store_a, store_b])
    session.flush()

    canonical = CanonicalIngredient(name="Organic Apples",
default_store_id=store_a.id)
    session.add(canonical)
    session.flush()

    item = GroceryItem(
        canonical_name="Organic Apples",
        quantity_display="3 lbs",
        original_quantity_display="3 lbs",
        category="PRODUCE",
        assigned_store="King Soopers",
        recipes=["Apple Pie"],
        is_active=True,
        is_checked=False,
    )
    session.add(item)
    session.commit()

    # Reassign store to Trader Joe's and set save_as_default=True
    response = client.patch(
        f"/grocery-list/items/{item.id}",
        json={"assigned_store": "Trader Joe's", "save_as_default":
True},
    )
    assert response.status_code == 200

    # Verify item override in database
    session.refresh(item)
    assert item.assigned_store_override == "Trader Joe's"

    # Verify CanonicalIngredient default store updated
    session.refresh(canonical)
    assert canonical.default_store_id == store_b.id


def test_update_item_quantity_retains_original_history(client,
session):
    """
    Asserts updating item quantity changes quantity_display while
preserving original_quantity_display.
    """
    item = GroceryItem(
        canonical_name="Whole Milk",
        quantity_display="1 gal",
        original_quantity_display="1 gal",
        category="DAIRY",
        assigned_store="King Soopers",
        recipes=["Pancakes"],
        is_active=True,
    )
    session.add(item)
    session.commit()

    # Update quantity display
    response = client.patch(
        f"/grocery-list/items/{item.id}",
        json={"quantity_display": "2 gal"},
    )
    assert response.status_code == 200

    session.refresh(item)
    assert item.quantity_display == "2 gal"
    assert item.original_quantity_display == "1 gal"


def test_soft_delete_and_restore_grocery_item(client, session):
    """
    Asserts soft deleting an item sets is_deleted=True and
excludes it from store groups in GET /current,
    moving it to deleted_items history. Restoring sets
is_deleted=False.
    """
    item = GroceryItem(
        canonical_name="Unsalted Butter",
        quantity_display="1 stick",
        original_quantity_display="1 stick",
        category