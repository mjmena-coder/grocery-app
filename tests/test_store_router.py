# tests/test_store_router.py

from backend.services.store_router import StoreRouter


def test_category_routing():
    """Verify specialty categories (meat, seafood) route to Whole Foods."""
    assert StoreRouter.assign_store("ribeye steak", "meat") == "Whole Foods"
    assert StoreRouter.assign_store("salmon fillet", "seafood") == "Whole Foods"


def test_keyword_routing():
    """Verify keywords (Dirty Dozen, milk, etc.) route to Whole Foods regardless of category."""
    assert StoreRouter.assign_store("organic milk", "dairy") == "Whole Foods"
    assert StoreRouter.assign_store("fresh spinach", "produce") == "Whole Foods"
    assert StoreRouter.assign_store("jalapeno peppers", "produce") == "Whole Foods"


def test_default_fallback():
    """Verify items not matching specialty categories or keywords default to King Soopers."""
    assert StoreRouter.assign_store("pinto beans", "pantry") == "King Soopers"
    assert StoreRouter.assign_store("paper towels", "household") == "King Soopers"