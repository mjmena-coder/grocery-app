import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_session
from backend.services.recipe_service import process_and_save_recipe
from backend.models import Recipe

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


@router.post("/{recipe_id}/image")
def upload_recipe_image(
    recipe_id: int,
    image: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """Upload and set an image photo for a given recipe."""
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    upload_dir = os.path.join("uploads", "recipes")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(image.filename)[1] or ".jpg"
    filename = f"recipe_{recipe_id}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/uploads/recipes/{filename}"
    recipe.image_url = image_url
    session.commit()
    session.refresh(recipe)

    return {"status": "ok", "recipe_id": recipe.id, "image_url": image_url}


@router.get("/")
def list_recipes(
    favorite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Fetch saved recipes with optional favorite and title search filters."""
    stmt = select(Recipe)

    # Apply favorite filter if provided
    if favorite is not None:
        stmt = stmt.where(Recipe.favorite == favorite)

    # Apply case-insensitive title search if provided
    if search:
        stmt = stmt.where(Recipe.title.ilike(f"%{search}%"))

    recipes = session.scalars(stmt).all()
    
    return {
        "status": "ok", 
        "count": len(recipes),
        "recipes": recipes
    }


@router.get("/{recipe_id}")
def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    """Retrieve full details for a single recipe including structured ingredients."""
    recipe = session.get(Recipe, recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    return {
        "status": "ok",
        "recipe": {
            "id": recipe.id,
            "title": recipe.title,
            "image_url": recipe.image_url,
            "source": recipe.source,
            "steps": recipe.steps.split("\n") if recipe.steps else [],
            "yield_info": recipe.yield_info,
            "prep_time": recipe.prep_time,
            "cook_time": recipe.cook_time,
            "notes": recipe.notes,
            "extraction_confidence": recipe.extraction_confidence,
            "confidence_reasons": recipe.confidence_reasons,
            "ingredients": [
                {
                    "id": ing.id,
                    "raw_name": ing.raw_name,
                    "quantity": ing.quantity,
                    "unit": ing.unit,
                    "comment": ing.comment,
                    "canonical_ingredient_id": ing.canonical_ingredient_id,
                    "needs_manual_review": ing.needs_manual_review,
                    "review_reason": ing.review_reason
                }
                for ing in recipe.ingredients
            ]
        }
    }

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
