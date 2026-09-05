from unittest.mock import patch
import pytest
from sqlalchemy import select
from backend.models import GroceryItem, Store, CanonicalIngredient


def test_update_item_store_reassignment(client, session):
    """
    Asserts a grocery list item can be moved from one store to another.
    When save_as_default is True, updates the CanonicalIngredient default store preference.
    """
    store_a = Store(name="King Soopers")
    store_b = Store(name="Trader Joe's")
    session.add_all([store_a, store_b])
    session.flush()

    canonical = CanonicalIngredient(name="Organic Apples", default_store_id=store_a.id)
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
        json={"assigned_store": "Trader Joe's", "save_as_default": True},
    )
    assert response.status_code == 200

    # Verify item override in database
    session.refresh(item)
    assert item.assigned_store_override == "Trader Joe's"

    # Verify CanonicalIngredient default store updated
    session.refresh(canonical)
    assert canonical.default_store_id == store_b.id


def test_update_item_quantity_retains_original_history(client, session):
    """
    Asserts updating item quantity changes quantity_display while preserving original_quantity_display.
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
    Asserts soft deleting an item sets is_deleted=True and excludes it from store groups in GET /current,
    moving it to deleted_items history. Restoring sets is_deleted=False.
    """
    item = GroceryItem(
        canonical_name="Unsalted Butter",
        quantity_display="1 stick",
        original_quantity_display="1 stick",
        category="DAIRY",
        assigned_store="King Soopers",
        recipes=["Cookies"],
        is_active=True,
        is_deleted=False,
    )
    session.add(item)
    session.commit()

    # Soft delete via endpoint
    res_delete = client.delete(f"/grocery-list/items/{item.id}")
    assert res_delete.status_code == 200

    session.refresh(item)
    assert item.is_deleted is True
    assert item.deleted_at is not None

    # Fetch current list and verify it is under deleted_items
    res_current = client.get("/grocery-list/current")
    assert res_current.status_code == 200
    data = res_current.json()
    assert any(d["id"] == item.id for d in data["deleted_items"])

    # Restore item via patch
    res_restore = client.patch(
        f"/grocery-list/items/{item.id}",
        json={"is_deleted": False},
    )
    assert res_restore.status_code == 200

    session.refresh(item)
    assert item.is_deleted is False


def test_generate_grocery_list_clears_old_records(client, session):
    """
    Asserts generating a new grocery list purges all prior grocery items from the database.
    """
    old_active = GroceryItem(
        canonical_name="Old Apples",
        category="PRODUCE",
        assigned_store="King Soopers",
        recipes=["Old Pie"],
        is_active=True,
    )
    old_deleted = GroceryItem(
        canonical_name="Old Milk",
        category="DAIRY",
        assigned_store="King Soopers",
        recipes=["Old Cereal"],
        is_active=False,
        is_deleted=True,
    )
    session.add_all([old_active, old_deleted])
    session.commit()

    with patch("backend.api.routes.grocery_list.build_consolidated_list") as mock_build:
        mock_build.return_value = {
            "items": [
                {
                    "canonical_name": "New Carrots",
                    "quantity_display": "2 lbs",
                    "category": "PRODUCE",
                    "assigned_store": "King Soopers",
                    "recipes": ["Stew"],
                }
            ],
            "kitchen_staples": [],
        }

        res = client.post("/grocery-list/generate", json={"recipe_ids": [1]})
        assert res.status_code == 200

    all_items = session.scalars(select(GroceryItem)).all()
    assert len(all_items) == 1
    assert all_items[0].canonical_name == "New Carrots"
