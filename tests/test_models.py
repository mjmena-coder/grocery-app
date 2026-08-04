from sqlalchemy.orm import Session

from backend.database import Base, engine, SessionLocal
from backend.models import Store, CanonicalIngredient, Recipe, Ingredient


def setup_module(module):
    Base.metadata.create_all(bind=engine)


def test_schema_holds_a_realistic_scenario():
    """
    Phase 0 gate check: can the schema represent one recipe, with an
    ingredient linked to a canonical ingredient and a default store,
    without needing any redesign?
    """
    session: Session = SessionLocal()
    try:
        king_soopers = Store(
            name="King Soopers", aisle_order={"produce": 1, "pantry": 2}
        )
        onion = CanonicalIngredient(
            name="yellow onion",
            category="produce",
            dirty_dozen=False,
            default_store=king_soopers,
        )
        recipe = Recipe(title="Test Soup", source="Test Cookbook p.12")
        ingredient = Ingredient(
            recipe=recipe,
            canonical_ingredient=onion,
            raw_name="yellow onion",
            quantity=2,
            unit="whole",
        )

        session.add_all([king_soopers, onion, recipe, ingredient])
        session.commit()

        saved = session.query(Recipe).filter_by(title="Test Soup").first()
        assert saved is not None
        assert len(saved.ingredients) == 1
        assert saved.ingredients[0].canonical_ingredient.default_store.name == "King Soopers"
    finally:
        session.close()