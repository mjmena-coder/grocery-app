from backend.export import StoreItem, format_keep_text, KING_SOOPERS_AISLE_MAP

def test_keep_text_formatting():
    sample_items: list[StoreItem] = [
        {"canonical_name": "black pepper", "quantity_display": None, "category": "pantry"},
        {"canonical_name": "brown rice", "quantity_display": "1.5 cups", "category": "pantry"},
        {"canonical_name": "cucumber", "quantity_display": "1", "category": "produce"},
        {"canonical_name": "garlic", "quantity_display": "2 large cloves", "category": "produce"},
        {"canonical_name": "green cabbage", "quantity_display": "0.5", "category": "produce"},
    ]

    expected_output = (
        "Cucumber (1)\n"
        "Garlic (2 large cloves)\n"
        "Green Cabbage (0.5)\n"
        "Black Pepper\n"
        "Brown Rice (1.5 cups)"
    )

    output = format_keep_text(sample_items, KING_SOOPERS_AISLE_MAP)
    assert output == expected_output, f"Expected:\n{expected_output}\n\nGot:\n{output}"
    print("✓ Keep format regression test passed!")

if __name__ == "__main__":
    test_keep_text_formatting()