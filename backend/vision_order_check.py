"""
vision_order_check.py

Reading-order sanity check for Apple Vision's OCR output (VNRecognizeTextRequest,
via vision_ocr.py). Vision returns a flat, already-mostly-ordered list of lines
(no layout regions/blocks the way PPStructureV3 gave us), so this works directly
on consecutive-line vertical position instead of block-overlap logic.

Background: real-photo testing found Vision generally orders pages correctly
(including magazine-style layouts where a headnote paragraph is meant to be
read before ingredient columns, even though the columns sit physically higher
on the page -- that's a large, legitimate backward jump in y-position). But on
at least one page (a narrow sidebar interleaved with a paragraph near the top),
Vision produced small backward jumps that were genuine ordering errors.

The two failure/non-failure cases are numerically distinguishable by jump
*magnitude*: legitimate section transitions were much larger (thousands of
pixels) than the observed error (tens to a few hundred pixels).

CONFIRMED LIMITATION (not hypothetical): tested against the full real page,
this magnitude-only approach produces a known false positive -- a legitimate
ingredient-column-1 -> column-2 transition (-540px) lands inside the same
magnitude range as a genuine ordering bug elsewhere (-266px), so no single
threshold can cleanly separate every case using y-position alone. Vision's
flat output gives us no column/region info to disambiguate further (unlike
the PPStructureV3 pipeline's block boundaries).

Treat this as a diagnostic a human glances at on a page that looks off, NOT
an automated pass/fail gate. A real fix would need genuine column/x-position
awareness, not a bigger or smaller number here.
"""

DEFAULT_MIN_FLAG = 30
DEFAULT_MAX_FLAG = 900


def check_order(lines, min_flag=DEFAULT_MIN_FLAG, max_flag=DEFAULT_MAX_FLAG):
    """
    lines: list of {"text": str, "score": float, "box": [x1, y1, x2, y2]},
           in the order Vision returned them (as produced by vision_ocr.py).

    Returns a list of warning strings for each consecutive pair where line i
    lands backward of line i-1 by an amount in [min_flag, max_flag] pixels --
    too small to be a normal section/column change, worth a manual look.

    Empty list = nothing suspicious.
    """
    warnings = []
    for i in range(1, len(lines)):
        dy = lines[i]["box"][1] - lines[i - 1]["box"][1]
        if -max_flag <= dy <= -min_flag:
            warnings.append(
                f"Line {i} ('{lines[i]['text'][:40]}') jumps backward {dy:.0f}px "
                f"from line {i - 1} ('{lines[i - 1]['text'][:40]}') -- "
                f"too small to be a normal section change, verify manually."
            )
    return warnings