# tests/test_consolidation.py

from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import patch

from backend.models import Recipe, Ingredient
from backend.services.consolidation import build_consolidated_list
import pytest


def test_build_consolidated_list_empty(session):
    """Verify empty list is returned when no ingredients match."""
    result = build_consolidated_list(session, recipe_ids=[999])
    assert result == {'items': [], 'kitchen_staples': []}


@patch("backend.services.consolidation.consolidate_ingredients")
def test_build_consolidated_list_with_items(mock_consolidate, session):
    """Verify build_consolidated_list integrates DB models, StoreRouter, and recipe provenance."""
    from backend.models import CanonicalIngredient

    # 1. Seed recipe, canonical ingredient, and ingredient in test DB
    recipe = Recipe(title="Green Smoothie", steps="Blend ingredients.")
    session.add(recipe)
    session.commit()

    canonical = CanonicalIngredient(name="spinach", category="PRODUCE")
    session.add(canonical)
    session.commit()

    ing = Ingredient(
        recipe_id=recipe.id,
        raw_name="2 cups spinach",
        quantity=2.0,
        unit="cup",
        canonical_ingredient_id=canonical.id,
    )
    session.add(ing)
    session.commit()

    # 2. Mock output from backend.consolidation_engine for canonical items and kitchen staples calls
    mock_consolidate.side_effect = [
        [
            {
                "name": "spinach",
                "quantity": 2.0,
                "unit": "cup",
                "quantity_display": "2 cups",
                "source_ingredient_ids": [ing.id],
            }
        ],
        [],  # kitchen staples call returns empty
    ]

    # 3. Call consolidation service
    result = build_consolidated_list(session, recipe_ids=[recipe.id])

    # 4. Assert against output structure built in consolidation.py
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["canonical_name"] == "spinach"
    assert item["quantity_display"] == "2 cups"
    assert item["category"] == "PRODUCE"
    assert item["recipes"] == ["Green Smoothie"]
