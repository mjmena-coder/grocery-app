import re
from typing import Optional
from ingredient_parser import parse_ingredient as _parse_ingredient_nlp

LEADING_TOKEN_FIXES = {"|": "1", "I": "1", "l": "1"}

def _strip_leading_noise_tokens(line: str) -> str:
    """
    Drop leading tokens that look like bullet-OCR noise (a stray single
    character, standalone punctuation) until reaching something that
    looks like the real start of the line: a digit/fraction, or a token
    we can normalize into one (common 1/I/l/| OCR confusions).
    """
    tokens = line.split()
    start = 0
    while start < len(tokens):
        token = tokens[start].strip(".,()")
        if re.match(r"^[\d½¼¾⅓⅔⅛⅜⅝⅞]", token):
            break
        if token in LEADING_TOKEN_FIXES:
            tokens[start] = LEADING_TOKEN_FIXES[token]
            break
        if len(token) <= 1:
            start += 1
            continue
        break
    return " ".join(tokens[start:])


def _amount_to_quantity_unit(amounts: list) -> tuple[Optional[float], Optional[str], bool]:
    """
    Reduce the library's amount list to a single (quantity, unit) pair
    plus an is_ambiguous flag. A single amount is the normal case. Zero
    amounts means no quantity was stated (e.g. "salt to taste") -- not
    itself a problem. More than one amount (seen on real OCR output,
    e.g. a stray slash splitting "1 1/2 cups" into two separate parsed
    amounts) means the parser got confused -- surface it rather than
    silently picking one.
    """
    if not amounts:
        return None, None, False
    if len(amounts) > 1:
        first = amounts[0]
        unit = str(first.unit) if first.unit else None
        return float(first.quantity), unit, True

    amt = amounts[0]
    quantity = float(amt.quantity)
    if amt.quantity != amt.quantity_max:
        quantity = float((amt.quantity + amt.quantity_max) / 2)
    unit = str(amt.unit) if amt.unit else None
    return quantity, unit, bool(amt.RANGE)


def parse_ingredient_line(line: str) -> dict:
    """
    Parse a single VLM'd ingredient line into quantity/unit/name/comment
    via ingredient-parser-nlp. Any exception, missing name, multiple
    candidate names, or multiple parsed amounts is flagged for manual
    review rather than guessed at -- mirrors the ingredient_slicer
    bake-off finding that confident-but-wrong output (e.g. '148 cups'
    from garbled input) is worse than no output.
    """
    line = _strip_leading_noise_tokens(line)

    if not line:
        return {
            "quantity": None, "unit": None, "raw_name": line, "comment": None,
            "needs_manual_review": True,
            "review_reason": "empty line",
        }

    try:
        parsed = _parse_ingredient_nlp(line)
    except Exception as exc:
        return {
            "quantity": None, "unit": None, "raw_name": line, "comment": None,
            "needs_manual_review": True,
            "review_reason": f"parser exception: {exc}",
        }

    if not parsed.name:
        return {
            "quantity": None, "unit": None, "raw_name": line, "comment": None,
            "needs_manual_review": True,
            "review_reason": "no ingredient name extracted",
        }

    names = [n.text.strip() for n in parsed.name if n.text.strip()]
    name = " or ".join(names) if names else None
    if not name:
        return {
            "quantity": None, "unit": None, "raw_name": line, "comment": None,
            "needs_manual_review": True,
            "review_reason": "no ingredient name extracted",
        }

    comment_parts = []
    if parsed.preparation:
        comment_parts.append(parsed.preparation.text.strip())
    if parsed.comment:
        comment_parts.append(parsed.comment.text.strip())
    comment = "; ".join(p for p in comment_parts if p) or None

    quantity, unit, ambiguous_quantity = _amount_to_quantity_unit(parsed.amount)
    if unit in {"ib", "ibs"}:
        unit = "lb"

    needs_manual_review = False
    review_reason = None
    if len(names) > 1:
        needs_manual_review = True
        review_reason = "multiple candidate ingredient names extracted"
    elif len(parsed.amount) > 1:
        needs_manual_review = True
        review_reason = "multiple quantities parsed for one line -- likely OCR corruption"

    result = {
        "quantity": quantity,
        "unit": unit,
        "raw_name": name,
        "comment": comment,
        "needs_manual_review": needs_manual_review,
    }
    if review_reason:
        result["review_reason"] = review_reason
    if ambiguous_quantity:
        result["ambiguous_quantity"] = True
    return result