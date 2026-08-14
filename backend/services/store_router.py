# backend/services/store_router.py
from typing import List, Set

class StoreRouter:
    DEFAULT_STORE: str = "King Soopers"
    SPECIALTY_STORE: str = "Whole Foods"

    SPECIALTY_CATEGORIES: Set[str] = {"meat", "seafood"}

    # Keyword overrides (Dirty Dozen + user specific preferences)
    SPECIALTY_KEYWORDS: List[str] = [
        "milk",
        "strawberry", "strawberries",
        "spinach", "kale", "collard",
        "grape", "peach", "pear", "nectarine",
        "apple", "bell pepper", "hot pepper", "jalapeno",
        "cherry", "cherries", "blueberry", "blueberries",
        "green bean", "tomato", "tomatoes"
    ]

    @classmethod
    def assign_store(cls, item_name: str, category: str) -> str:
        """Determines target store based on category and keyword rules."""
        name = (item_name or "").lower()
        cat = (category or "").lower()

        # 1. Category-level routing (e.g., all meat/seafood to WF)
        if cat in cls.SPECIALTY_CATEGORIES:
            return cls.SPECIALTY_STORE

        # 2. Keyword-level routing (Dirty Dozen + custom preferences)
        if any(kw in name for kw in cls.SPECIALTY_KEYWORDS):
            return cls.SPECIALTY_STORE

        # 3. Default fallback
        return cls.DEFAULT_STORE