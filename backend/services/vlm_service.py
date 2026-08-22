import json
import os
from typing import List, Optional
import subprocess
import urllib.request
import time
from fastapi import HTTPException
from pydantic import BaseModel, Field
import ollama

VLM_MODEL = os.getenv("VLM_MODEL", "qwen2.5vl:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


class ParsedIngredientSchema(BaseModel):
    raw_text: str = Field(
        description="Original full line from recipe, e.g., '2 tablespoons finely chopped organic spinach'"
    )
    canonical_name: str = Field(
        description="Clean, lowercased base ingredient name stripped of quantities, units, and prep instructions, e.g., 'spinach'"
    )
    quantity: Optional[float] = Field(
        None, description="Numeric quantity parsed as a float (e.g. 1.5 for '1 1/2'), or null if unstated"
    )
    unit: Optional[str] = Field(
        None, description="Standardized measurement unit (e.g., 'cup', 'tbsp', 'clove', 'oz'), or null for count items"
    )
    size_descriptor: Optional[str] = Field(
        None, 
        description="Physical size, length, or dimensional descriptor (e.g., '1-inch', 'large', 'medium', '3-cm'), or null if absent"
    )
    comment: Optional[str] = Field(
            None, description="Preparation notes, quality adjectives, or state (e.g., 'finely chopped', 'fresh', 'peeled and grated'), or null if absent"
    )
    category: str = Field(
        "General",
        description="Must be strictly one of: PRODUCE, PANTRY, MEAT, DAIRY, FROZEN, BAKERY, GENERAL."
    )
    is_dirty_dozen: bool = Field(
        False,
        description="Set to true if this item is on the Dirty Dozen high-pesticide produce list (e.g. spinach, strawberries, kale, apples, peaches, nectarines, grapes, bell peppers, cherries, blueberries, green beans, pears)"
    )
    organic_considerations: bool = Field(
        False,
        description="Set to true if this item should be considered to be bought organic."
    )


class VLMRecipeSchema(BaseModel):
    """Pydantic schema used solely to enforce Ollama's JSON output format."""
    title: str = Field(description="Primary title of the recipe")
    yield_info: Optional[str] = Field(None, description="Serving size or yield")
    prep_time: Optional[str] = Field(None, description="Preparation time")
    cook_time: Optional[str] = Field(None, description="Cooking time")
    ingredients: List[ParsedIngredientSchema] = Field(
        description="Structured ingredient list with parsed quantities, canonical names, categories, and flags"
    )
    steps: List[str] = Field(description="Chronological step-by-step cooking instructions")
    notes: Optional[List[str]] = Field(None, description="Dietary notes, FODMAP warnings, or sidebar tips")


EXTRACTION_PROMPT = """Analyze this cookbook page image and extract structured JSON matching the requested schema.

Instructions:
1. Extract Title, Yield, Prep Time, Cook Time, Steps, and Notes.
2. For each ingredient:
   - raw_text: preserve full line context (e.g., '2 cups greens, finely chopped').
   - canonical_name: extract lowercased base noun (e.g. 'basil', 'ginger').
   - quantity: convert fractions or whole numbers to float (e.g., 2.0).
   - unit: isolate STRICT measurement units ONLY (e.g., 'cup', 'tbsp', 'clove', 'oz', 'piece'). NEVER include prep words like 'chopped' or adjectives like 'fresh'.
   - size_descriptor: extract ONLY physical size/dimensions (e.g., '1-inch', 'large', 'medium', '3-cm'). NEVER include prep actions like 'chopped', 'diced', 'minced', 'grated'.
   - comment: place all prep instructions, quality notes, and state descriptions here (e.g., 'finely chopped', 'fresh', 'peeled and grated').
   - is_dirty_dozen: mark true for high-pesticide produce items (spinach, strawberries, kale, grapes, apples, peppers, etc.).
   - is organic_considerations: mark true for items that should be considered bought organic (pregnancy or general health reasons).
   - category: MUST be classified into EXACTLY one of these options:
       * PRODUCE: Fresh vegetables, fruits, fresh herbs, root crops, squash (e.g., 'tomato', 'celery', 'basil', 'yuca', 'corn', 'chayote', 'plantain', 'cabbage', 'squash').
       * PANTRY: Oils, vinegars, dried spices/herbs, seeds, sauces, canned goods, broths, seasonings (e.g., 'soy sauce', 'sesame seeds', 'bay leaf', 'bouillon', 'salt').
       * MEAT: Fresh/frozen raw or processed meats, poultry, seafood, bacon, sausage.
       * DAIRY: Milk, butter, cheeses, yogurt, eggs, cream.
       * FROZEN: Commercial freezer aisle items.
       * BAKERY: Pre-baked fresh bread, rolls, tortillas.
       * GENERAL: Tap water, non-food items, or completely unclassifiable goods.3. Multi-column / wrapped ingredients: reassemble broken lines into clean strings before parsing.
4. Steps: Extract all cooking steps in chronological order.
5. Sidebar / Notes: Place FODMAP advice or sidebar tips into notes.
"""


def extract_recipe_from_image(image_path: str, model_name: str = VLM_MODEL) -> VLMRecipeSchema:
    """Uses Qwen2.5-VL to extract structured recipe data."""
    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT, "images": [image_path]}],
        format=VLMRecipeSchema.model_json_schema(),
        options={"temperature": 0.1, "num_ctx": 8192},
    )
    structured_data = json.loads(response["message"]["content"])
    return VLMRecipeSchema(**structured_data)