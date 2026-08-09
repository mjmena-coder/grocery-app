"""
Regression tests for vision_order_check.py, built from real Apple Vision
OCR output (VNRecognizeTextRequest) on actual cookbook photos.

  - fixtures_fiber_fueled_vision.json: KNOWN reading-order bug -- a narrow
    sidebar ("11 Plant Points" / "Makes 2 bowls") gets interleaved with the
    headnote paragraph beside it. Two small backward y-jumps mark it.
  - fixtures_quick_cozy_vision.json: a large, LEGITIMATE backward y-jump
    (headnote paragraph finishes, then ingredient column 1 begins near the
    top of the page again) -- must NOT be flagged.
"""
import json
from backend.vision_order_check import check_order
from pathlib import Path


def load(path):
    with open(path) as f:
        return json.load(f)


def test_fiber_fueled_known_bug_is_flagged():
    lines = load(Path(__file__).parent / "fixtures" /  "fixtures_fiber_fueled_vision.json")
    warnings = check_order(lines)
    assert len(warnings) == 2
    assert any("and flavor. I highly recommend" in w for w in warnings)
    assert any("FODMAP note" in w for w in warnings)


def test_quick_cozy_full_page_has_known_false_positive():
    """
    Honest limitation, not swept under the rug: a magnitude-only check
    cannot distinguish every legitimate column transition from a real
    error using Vision's flat list alone (no column/region info to lean
    on, unlike the PPStructureV3 pipeline). The column1->column2 jump
    here (-540px) is legitimate but lands inside the same magnitude range
    as real bugs elsewhere (-266px), so it gets flagged too.

    This test locks in that KNOWN false positive so it doesn't silently
    change, rather than asserting zero warnings (which is not true of the
    real data). Treat this check as a diagnostic a human glances at, not
    an authoritative pass/fail gate, until it's rebuilt with real column
    awareness.
    """
    lines = load(Path(__file__).parent / "fixtures" /  "fixtures_quick_cozy_vision.json")
    warnings = check_order(lines)
    assert len(warnings) == 1
    assert "3 tablespoons low-sodium" in warnings[0]


def test_quick_cozy_headnote_to_ingredients_jump_is_large():
    """
    Sanity check on the underlying assumption: the legitimate jump in
    Quick & Cozy really is far larger in magnitude than the erroneous
    jumps in Fiber Fueled, which is what justifies using a magnitude
    threshold to tell them apart at all.
    """
    lines = load(Path(__file__).parent / "fixtures" /  "fixtures_quick_cozy_vision.json")
    headnote_end_idx = next(
        i for i, l in enumerate(lines) if "old-school TV shows" in l["text"]
    )
    ingredients_start_idx = headnote_end_idx + 1
    dy = (
        lines[ingredients_start_idx]["box"][1]
        - lines[headnote_end_idx]["box"][1]
    )
    assert dy < -2000  # confirmed ~-2947px in real data


def test_fiber_fueled_warnings_reference_correct_line_indices():
    lines = load(Path(__file__).parent / "fixtures" /  "fixtures_fiber_fueled_vision.json")
    warnings = check_order(lines)
    # line 4 ("and flavor...") and line 7 ("FODMAP note...") are the two
    # known bad transitions -- confirm the check is pointing at exactly
    # those, not some other coincidental backward jump later in the page
    assert "Line 4 (" in warnings[0]
    assert "Line 7 (" in warnings[1]