# tests/test_consolidation.py

from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import patch

from backend.models import Recipe, Ingredient
from backend.services.consolidation import build_consolidated_list
import pytest


@dataclass
class MockConsolidatedItem:
    id: int
    canonical_name: str
    quantity: Optional[float]
    unit: Optional[str]
    category: str
    source_ingredient_ids: List[int]


def test_build_consolidated_list_empty(session):
    """Verify empty list is returned when no ingredients match."""
    result = build_consolidated_list(session, recipe_ids=[999])
    assert result == {'items': [], 'kitchen_staples': []}


@patch("backend.services.consolidation.consolidate_ingredients")
def test_build_consolidated_list_with_items(mock_consolidate, session):
    """Verify build_consolidated_list integrates DB models, StoreRouter, and recipe provenance."""
    # 1. Seed recipe and ingredient in test DB
    recipe = Recipe(title="Green Smoothie", steps="Blend ingredients.")
    session.add(recipe)
    session.commit()

    ing = Ingredient(
        recipe_id=recipe.id,
        raw_name="2 cups spinach",
        quantity=2.0,
        unit="cup",
    )
    session.add(ing)
    session.commit()

    # 2. Mock output from backend.consolidation_engine
    mock_consolidate.return_value = [
        MockConsolidatedItem(
            id=1,
            canonical_name="spinach",
            quantity=2.0,
            unit="cup",
            category="produce",
            source_ingredient_ids=[ing.id],
        )
    ]

    # 3. Call consolidation service
    result = build_consolidated_list(session, recipe_ids=[recipe.id])

    # 4. Assert against output structure built in consolidation.py
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["canonical_name"] == "spinach"
    assert item["quantity_display"] == "2.0 cup"
    assert item["category"] == "PRODUCE"
    assert item["assigned_store"] == "Whole Foods"  # Keyword 'spinach' routes to Whole Foods via StoreRouter
    assert item["recipes"] == ["Green Smoothie"]
