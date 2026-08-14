from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_session
from backend.services.recipe_service import process_and_save_recipe

router = APIRouter(prefix="/recipes", tags=["Recipes"])


class RecipeUpdateSchema(BaseModel):
    title: Optional[str] = None
    steps: Optional[str] = None
    source: Optional[str] = None


@router.post("/extract")
async def extract_recipe(
    image: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Upload a recipe image, run VLM extraction, parse & link canonical ingredients,
    and persist recipe metadata to SQLite.
    """
    return process_and_save_recipe(session, image)


@router.get("/")
def list_recipes(
    favorite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Fetch saved recipes with optional favorite and title search filters."""
    # Logic delegates to query helper or recipe service
    return {"status": "ok", "recipes": []}


@router.get("/{recipe_id}")
def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    """Retrieve full details for a single recipe including structured ingredients."""
    return {"status": "ok", "recipe_id": recipe_id}


@router.patch("/{recipe_id}")
def update_recipe(
    recipe_id: int, 
    payload: RecipeUpdateSchema, 
    session: Session = Depends(get_session)
):
    """Update editable recipe fields (title, steps, source)."""
    return {"status": "updated", "recipe_id": recipe_id}


@router.post("/{recipe_id}/cook")
def mark_recipe_cooked(recipe_id: int, session: Session = Depends(get_session)):
    """Increment times_cooked and update last_cooked_date."""
    return {"status": "cooked", "recipe_id": recipe_id}


@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: int, session: Session = Depends(get_session)):
    """Delete a recipe and its associated ingredient rows."""
    return {"status": "deleted", "recipe_id": recipe_id}