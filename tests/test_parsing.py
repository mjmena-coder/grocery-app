from backend.parsing import parse_ingredient_line, segment_lines


def test_parse_simple_ingredient():
    result = parse_ingredient_line("2 cups diced yellow onion")
    assert result == {"quantity": 2, "unit": "cups", "raw_name": "diced yellow onion"}


def test_parse_fraction_ingredient():
    result = parse_ingredient_line("1/2 tsp salt")
    assert result == {"quantity": 0.5, "unit": "tsp", "raw_name": "salt"}


def test_parse_mixed_number_ingredient():
    result = parse_ingredient_line("1 1/2 cups flour")
    assert result == {"quantity": 1.5, "unit": "cups", "raw_name": "flour"}


def test_parse_no_unit_ingredient():
    result = parse_ingredient_line("3 eggs")
    assert result == {"quantity": 3, "unit": None, "raw_name": "eggs"}


def test_segment_lines_splits_ingredients_from_steps():
    text = (
        "2 cups flour\n"
        "1 tsp salt\n"
        "Preheat oven to 350 degrees.\n"
        "Mix dry ingredients together.\n"
    )
    ingredients, steps = segment_lines(text)
    assert ingredients == ["2 cups flour", "1 tsp salt"]
    assert steps == [
        "Preheat oven to 350 degrees.",
        "Mix dry ingredients together.",
    ]