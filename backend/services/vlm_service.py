import json
import os
from typing import List, Optional
import subprocess
import urllib.request
from fastapi import HTTPException
from pydantic import BaseModel, Field
import ollama

VLM_MODEL = os.getenv("VLM_MODEL", "qwen2.5vl:7b")


class VLMRecipeSchema(BaseModel):
    """Pydantic schema used solely to enforce Ollama's JSON output format."""
    title: str = Field(description="Primary title of the recipe")
    yield_info: Optional[str] = Field(None, description="Serving size or yield")
    prep_time: Optional[str] = Field(None, description="Preparation time")
    cook_time: Optional[str] = Field(None, description="Cooking time")
    ingredients: List[str] = Field(description="Complete list of ingredients with quantities and units")
    steps: List[str] = Field(description="Chronological step-by-step cooking instructions")
    notes: Optional[List[str]] = Field(None, description="Dietary notes, FODMAP warnings, or sidebar tips")


EXTRACTION_PROMPT = """Analyze this cookbook page image and extract structured JSON matching the requested schema.

Instructions:
1. Extract Title, Yield, Prep Time, Cook Time, Ingredients, and Steps.
2. Multi-column / wrapped ingredients: Look at the visual flow. Reassemble broken ingredient lines into clean, full strings (e.g. "1 teaspoon garlic-infused olive oil (or neutral oil, broth, or water)").
3. Steps: Extract all cooking steps in chronological order.
4. Sidebar / Notes: Place FODMAP advice, page references, or dietary badges into the `notes` list rather than ingredients.
"""

def ensure_ollama_running() -> bool:
    """Checks if Ollama server is active, attempting background launch if down."""
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5):
            return True
    except Exception:
        pass

    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Ollama service is not running and could not be started automatically."
        )


def extract_recipe_from_image(image_path: str, model_name: str = VLM_MODEL) -> VLMRecipeSchema:
    """Verifies Ollama is running, then uses Qwen2.5-VL to extract structured recipe data."""
    # ensure_ollama_running()
    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT, "images": [image_path]}],
        format=VLMRecipeSchema.model_json_schema(),
        options={"temperature": 0.1, "num_ctx": 8192},
    )
    structured_data = json.loads(response["message"]["content"])
    return VLMRecipeSchema(**structured_data)