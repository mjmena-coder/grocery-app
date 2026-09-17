from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from io import BytesIO

from backend.models import Recipe, Ingredient
from backend.services.recipe_service import process_and_save_recipe
from backend.services.vlm_service import ParsedIngredientSchema, VLMRecipeSchema

import pytest


@patch("backend.services.recipe_service.extract_recipe_from_image")
def test_process_and_save_recipe_full_metadata(mock_extract, session):
    # Mock VLM extraction result with full metadata
    mock_extract.return_value = VLMRecipeSchema(
        title="Roasted Garlic Pasta",
        yield_info="Serves 4",
        prep_time="15 mins",
        cook_time="20 mins",
        ingredients=[
            ParsedIngredientSchema(
                raw_text="8 oz pasta",
                canonical_name="pasta",
                quantity=8.0,
                unit="oz",
                category="PASTA",
            ),
            ParsedIngredientSchema(
                raw_text="4 cloves garlic",
                canonical_name="garlic",
                quantity=4.0,
                unit="cloves",
                category="PRODUCE",
            ),
        ],
        steps=["Boil pasta.", "Sauté garlic."],
        notes=["Use gluten-free pasta if needed."],
    )

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


@patch("backend.services.recipe_service.extract_recipe_from_image")
@patch("backend.services.recipe_service.process_uploaded_image_bytes")
def test_process_and_save_recipe_heic_image_processing(mock_process, mock_extract, session):
    mock_vlm_recipe = MagicMock()
    mock_vlm_recipe.title = "HEIC Test Recipe"
    mock_vlm_recipe.steps = ["Step 1"]
    mock_vlm_recipe.yield_info = "2 servings"
    mock_vlm_recipe.prep_time = "10 mins"
    mock_vlm_recipe.cook_time = "15 mins"
    mock_vlm_recipe.notes = None
    mock_vlm_recipe.ingredients = []
    mock_extract.return_value = mock_vlm_recipe

    mock_process.return_value = (b"processed_bytes", ".jpg")

    upload_file = UploadFile(filename="photo.heic", file=BytesIO(b"raw_heic_data"))

    result = process_and_save_recipe(session, upload_file)

    assert result["title"] == "HEIC Test Recipe"
    mock_process.assert_called_once_with(b"raw_heic_data", "photo.heic")
