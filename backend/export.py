from typing import TypedDict, Optional

class StoreItem(TypedDict):
    canonical_name: str
    quantity_display: Optional[str]  # e.g., "2", "0.5 cups", "1.5"
    category: str                    # e.g., "produce", "pantry", "dairy"

# Example Aisle Order Mappings
KING_SOOPERS_AISLE_MAP = {
    "produce": 1,
    "deli": 2,
    "bakery": 3,
    "meat": 4,
    "pantry": 5,
    "frozen": 6,
    "dairy": 7,
    "other": 99
}

WHOLE_FOODS_AISLE_MAP = {
    "produce": 1,
    "floral": 2,
    "bakery": 3,
    "cheese": 4,
    "meat": 5,
    "pantry": 6,
    "dairy": 7,
    "frozen": 8,
    "other": 99
}

def sort_items_by_aisle(items: list[StoreItem], aisle_map: dict[str, int]) -> list[StoreItem]:
    """Sorts ingredient lines according to the store's aisle hierarchy."""
    return sorted(items, key=lambda x: aisle_map.get(x["category"].lower(), 99))


def format_keep_text(items: list[StoreItem], aisle_map: dict[str, int]) -> str:
    """
    Formats items into Google Keep pasteable text:
    - 1 item per line
    - Quantity folded into parentheses: 'Onions (2)' or 'Brown Rice (1.5 cups)'
    - No bullets, dashes, or blank lines
    - Sorted by store aisle order
    """
    sorted_items = sort_items_by_aisle(items, aisle_map)
    lines = []
    
    for item in sorted_items:
        name = item["canonical_name"].strip().title()
        qty = item.get("quantity_display")
        
        if qty:
            line = f"{name} ({qty})"
        else:
            line = name
            
        lines.append(line)
        
    return "\n".join(lines)