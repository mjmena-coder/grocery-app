from unittest.mock import patch
from fastapi import UploadFile
from io import BytesIO

from backend.models import Recipe, Ingredient
from backend.services.recipe_service import process_and_save_recipe

import pytest

@pytest.mark.skip(reason="Might be ok to delete.")
@patch("backend.services.recipe_service.ensure_ollama_running")
@patch("backend.services.recipe_service.extract_recipe_from_image")
def test_process_and_save_recipe_full_metadata(mock_extract, mock_ollama, session):
    # Mock VLM extraction result with full metadata
    class MockVLMRecipe:
        title = "Roasted Garlic Pasta"
        yield_info = "Serves 4"
        prep_time = "15 mins"
        cook_time = "20 mins"
        ingredients = ["8 oz pasta", "4 cloves garlic"]
        steps = ["Boil pasta.", "Sauté garlic."]
        notes = ["Use gluten-free pasta if needed."]

    mock_extract.return_value = MockVLMRecipe()

    # Create dummy upload file
    file = UploadFile(filename="test_recipe.jpg", file=BytesIO(b"fake image data"))

    result = process_and_save_recipe(session, file)

    assert result["recipe_id"] is not None
    assert result["title"] == "Roasted Garlic Pasta"
    assert result["yield_info"] == "Serves 4"

    # Verify DB persistence
    saved_recipe = session.get(Recipe, result["recipe_id"])
    assert saved_recipe is not None
    assert saved_recipe.prep_time == "15 mins"
    assert saved_recipe.cook_time == "20 mins"
    assert saved_recipe.yield_info == "Serves 4"
    assert saved_recipe.notes == ["Use gluten-free pasta if needed."]
    assert saved_recipe.extraction_confidence is not None
    assert len(saved_recipe.ingredients) == 2