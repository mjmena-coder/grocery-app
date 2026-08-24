import os
import tempfile
import shutil
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.models import Recipe, Ingredient
from backend.parsing import parse_ingredient_line
from backend.services.canonical_service import resolve_or_create_canonical_ingredient
from backend.services.vlm_service import extract_recipe_from_image
from backend.services.confidence_service import calculate_extraction_confidence
from backend.utils.kitchen_staples import KITCHEN_STAPLE_INGREDIENTS

def process_and_save_recipe(session: Session, image: UploadFile) -> dict:
    """
    Handles file upload, VLM extraction, metadata parsing, 
    canonical linking, and SQLite persistence.
    """
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
        # 3. Create parent Recipe record.
        recipe = Recipe(
            title=vlm_recipe.title,
            source=None, # TODO: Eventually populate this...
            steps="\n".join(vlm_recipe.steps), # TODO: Why is this joined? expects [str] but receives List[str]...
            yield_info=vlm_recipe.yield_info,
            prep_time=vlm_recipe.prep_time,
            cook_time=vlm_recipe.cook_time,
            notes=vlm_recipe.notes,     
            extraction_confidence=confidence,
            confidence_reasons=confidence_reasons,
        )

        # 4. Process each ingredient and link canonical ID
        for raw_ingredient in vlm_recipe.ingredients:
            parsed = parse_ingredient_line(raw_ingredient.raw_text)
            review_reason = ""
            needs_review = False
            canonical_id = None
            # Only create canonical if item name not kitchen staple.
            if KITCHEN_STAPLE_INGREDIENTS.search(parsed["raw_name"]):
                review_reason = parsed.get("review_reason")
                needs_review = parsed["needs_manual_review"]
            else:
                canonical_id = resolve_or_create_canonical_ingredient(session, raw_ingredient)
                if not canonical_id and not needs_review:
                    needs_review = True
                    review_reason = "unlinked ingredient: no matching canonical record found"

            # TODO: Needs to be cleaned up, there is a mix between parsing vs. VLM quantities.
            recipe.ingredients.append(Ingredient(
                raw_name=parsed["raw_name"],                                # Currently done better by parsing, raw_name vs raw_text.
                quantity=raw_ingredient.quantity,                           # Pull ingredient quantity directly.
                unit=parsed["unit"],                                        # Both do it, VLM halucinates, going with parsed since it uses ingredient_parser_nlp.
                size_descriptor=raw_ingredient.size_descriptor,             # VLM special.
                comment=parsed["comment"],                                  # VLM doesn't do anything like this.
                ambiguous_quantity=parsed.get("ambiguous_quantity", False), # VLM doesn't handle ambiguous quantity atm, just gives you quantity.
                needs_manual_review=needs_review,                           # VLM doesn't do anything like this right now.
                review_reason=review_reason,                                # VLM doesn't do anything like this.
                canonical_ingredient_id=canonical_id                        # Formerly omitted.
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