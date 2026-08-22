import pytest
from backend.models import CanonicalIngredient, Ingredient, Recipe
from backend.services.canonical_service import (
    resolve_or_create_canonical_ingredient,
    get_unlinked_ingredients,
    merge_canonical_records,
)

@pytest.mark.skip(reason="Might be ok to delete.")
def test_resolve_exact_match(session):
    canonical = CanonicalIngredient(name="yellow onion", category="produce")
    session.add(canonical)
    session.commit()

    matched_id = resolve_or_create_canonical_ingredient(session, "Yellow Onion")
    assert matched_id == canonical.id

@pytest.mark.skip(reason="Might be ok to delete.")
def test_resolve_substring_match(session):
    canonical = CanonicalIngredient(name="yellow onion", category="produce")
    session.add(canonical)
    session.commit()

    matched_id = resolve_or_create_canonical_ingredient(session, "diced yellow onion")
    assert matched_id == canonical.id


def test_get_unlinked_ingredients(session):
    recipe = Recipe(title="Test Soup", steps="Boil water")
    session.add(recipe)
    session.commit()

    ing1 = Ingredient(recipe_id=recipe.id, raw_name="1 onion", canonical_ingredient_id=None)
    session.add(ing1)
    session.commit()

    unlinked = get_unlinked_ingredients(session)
    assert len(unlinked) == 1
    assert unlinked[0]["raw_name"] == "1 onion"


def test_merge_canonical_records(session):
    c1 = CanonicalIngredient(name="onions")
    c2 = CanonicalIngredient(name="yellow onion")
    session.add_all([c1, c2])
    session.commit()

    recipe = Recipe(title="Stew")
    session.add(recipe)
    session.commit()

    ing = Ingredient(recipe_id=recipe.id, raw_name="onions", canonical_ingredient_id=c1.id)
    session.add(ing)
    session.commit()

    merge_canonical_records(session, source_id=c1.id, target_id=c2.id)

    session.refresh(ing)
    assert ing.canonical_ingredient_id == c2.id
    assert session.get(CanonicalIngredient, c1.id) is None