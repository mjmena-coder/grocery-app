import os
import tempfile
import shutil
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.models import Recipe, Ingredient
from backend.parsing import parse_ingredient_line
from backend.services.canonical_service import resolve_or_create_canonical_ingredient
from backend.services.vlm_service import extract_recipe_from_image, ensure_ollama_running
from backend.services.confidence_service import calculate_extraction_confidence

def process_and_save_recipe(session: Session, image: UploadFile) -> dict:
    """
    Handles file upload, VLM extraction, metadata parsing, 
    canonical linking, and SQLite persistence.
    """
    # ensure_ollama_running()

    # 1. Handle temporary file
    suffix = os.path.splitext(image.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(image.file, tmp)
        tmp_path = tmp.name

    try:
        vlm_recipe = extract_recipe_from_image(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # 2. Score extraction confidence
    confidence, confidence_reasons = calculate_extraction_confidence(vlm_recipe)

    try:
        # 3. Create parent Recipe record with ALL missing metadata
        recipe = Recipe(
            title=vlm_recipe.title,
            source=None,
            steps="\n".join(vlm_recipe.steps),
            yield_info=vlm_recipe.yield_info,      # Formerly dropped
            prep_time=vlm_recipe.prep_time,        # Formerly dropped
            cook_time=vlm_recipe.cook_time,        # Formerly dropped
            notes=vlm_recipe.notes,                # Formerly dropped
            extraction_confidence=confidence,      # Formerly dropped
            confidence_reasons=confidence_reasons, # Formerly dropped
        )

        # 4. Process each ingredient and link canonical ID
        for raw_ingredient in vlm_recipe.ingredients:
            parsed = parse_ingredient_line(raw_ingredient)
            canonical_id = resolve_or_create_canonical_ingredient(session, parsed["raw_name"])

            needs_review = parsed["needs_manual_review"]
            review_reason = parsed.get("review_reason")

            # Flag if parsed fine, but no canonical item was found
            if not canonical_id and not needs_review:
                needs_review = True
                review_reason = "unlinked ingredient: no matching canonical record found"

            recipe.ingredients.append(Ingredient(
                raw_name=parsed["raw_name"],
                quantity=parsed["quantity"],
                unit=parsed["unit"],
                comment=parsed["comment"],
                ambiguous_quantity=parsed.get("ambiguous_quantity", False),
                needs_manual_review=needs_review,
                review_reason=review_reason,
                canonical_ingredient_id=canonical_id  # Formerly omitted
            ))

        # 5. DB Commit boundary
        session.add(recipe)
        session.commit()
        session.refresh(recipe)

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")

    # 6. Format API response payload
    return {
        "recipe_id": recipe.id,
        "title": vlm_recipe.title,
        "yield_info": vlm_recipe.yield_info,
        "prep_time": vlm_recipe.prep_time,
        "cook_time": vlm_recipe.cook_time,
        "ingredients": vlm_recipe.ingredients,
        "steps": vlm_recipe.steps,
        "notes": vlm_recipe.notes,
        "extraction_confidence": confidence,
        "confidence_reasons": confidence_reasons,
    }