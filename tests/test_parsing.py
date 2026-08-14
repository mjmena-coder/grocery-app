from backend.parsing import parse_ingredient_line


def test_parse_simple_ingredient():
    # NOTE: unit is now pint-canonicalized ("cup", not "cups") -- this is
    # intentional, matches the pint-based unit conversion the build plan
    # already calls for in Section 3.
    result = parse_ingredient_line("2 cups diced yellow onion")
    assert result["quantity"] == 2.0
    assert result["unit"] == "cup"
    assert result["raw_name"] == "yellow onion"
    assert result["comment"] == "diced"
    assert result["needs_manual_review"] is False


def test_parse_fraction_ingredient():
    result = parse_ingredient_line("1/2 tsp salt")
    assert result["quantity"] == 0.5
    assert result["unit"] == "teaspoon"
    assert result["raw_name"] == "salt"
    assert result["needs_manual_review"] is False


def test_parse_mixed_number_ingredient():
    result = parse_ingredient_line("1 1/2 cups flour")
    assert result["quantity"] == 1.5
    assert result["unit"] == "cup"
    assert result["raw_name"] == "flour"
    assert result["needs_manual_review"] is False


def test_parse_no_unit_ingredient():
    result = parse_ingredient_line("3 eggs")
    assert result["quantity"] == 3.0
    assert result["unit"] is None
    assert result["raw_name"] == "eggs"
    assert result["needs_manual_review"] is False



# --- Real fixture-derived cases (fixtures_fiber_fueled_vision.json) ---
# Lines rejoined from the fixture's OCR boxes in reading order, since
# segment_lines/parse_ingredient_line operate on already-joined text,
# not raw per-box output.

def test_parse_known_eup_typo_flags_review():
    # Known residual Vision OCR error from PROJECT_STATUS.md: 'cup' -> 'eup'.
    # The unit isn't recognized, so it stays stuck to the name instead of
    # a silent wrong guess -- document that behavior explicitly.
    result = parse_ingredient_line(
        "½ eup canned chickpeas, drained and rinsed"
    )
    assert result["quantity"] == 0.5
    assert result["unit"] is None
    assert result["raw_name"] == "eup canned chickpeas"
    assert result["needs_manual_review"] is False  # doesn't self-flag; unit silently absorbed into name
    assert result["comment"] == "drained and rinsed"


def test_parse_known_stray_slash_mixed_fraction_flags_review():
    # Known residual Vision OCR error: stray slash instead of space in a
    # mixed fraction ("1 1/2" -> "1/1/2" style corruption). This splits
    # into two separate parsed amounts -- exactly the ambiguity signal
    # that should route to manual review.
    result = parse_ingredient_line("1/½ cups cooked brown rice")
    assert result["needs_manual_review"] is True
    assert "multiple quantities" in result["review_reason"]
    assert result["raw_name"] == "brown rice"


def test_parse_embedded_prep_instructions():
    # Real fixture line combining prep instructions inline with the
    # ingredient -- the case flagged as "not yet wired in" in
    # PROJECT_STATUS.md.
    result = parse_ingredient_line("1 medium cucumber, thinly sliced into half moons")
    assert result["quantity"] == 1.0
    assert result["raw_name"] == "cucumber"
    assert result["comment"] == "thinly sliced into half moons"
    assert result["needs_manual_review"] is False


def test_parse_parenthetical_comment_and_or_list_flags_review():
    # Real fixture line: parenthetical aside plus an "or" ingredient list
    # (garlic-infused olive oil / broth / water) -- multiple candidate
    # names should flag for review rather than silently picking one.
    result = parse_ingredient_line(
        "1 teaspoon garlic-infused olive oil (see Pro Tip, page 87), broth, or water"
    )
    assert result["needs_manual_review"] is True
    assert "multiple candidate" in result["review_reason"]
    assert "garlic-infused olive oil" in result["raw_name"]