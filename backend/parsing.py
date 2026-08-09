import re

UNIT_WORDS = {
    "cup", "cups", "tbsp", "tablespoon", "tablespoons",
    "tsp", "teaspoon", "teaspoons", "oz", "ounce", "ounces",
    "lb", "lbs", "ib", "ibs",  # "ib"/"ibs": common OCR misread of "lb"/"lbs"
    "pound", "pounds", "g", "gram", "grams", "kg", "ml", "l",
    "liter", "liters", "pinch", "clove", "cloves", "can", "cans",
}

INGREDIENTS_HEADER_RE = re.compile(r"^ingredients?\b", re.IGNORECASE)
DIRECTIONS_HEADER_RE = re.compile(
    r"^(directions?|instructions?|method|steps)\b", re.IGNORECASE
)

QUANTITY_RE = re.compile(
    r"^\s*(\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+\s*-\s*\d+|\d+)\s*"
)

LEADING_NOISE_RE = re.compile(r"^[^\w\d]+")  # strips bullet-OCR junk like "e ", "• "

# Standalone single-char tokens Tesseract commonly confuses with the
# numeral 1 -- only applied to the very first token of a line, since
# ingredient lines almost always start with a quantity.
LEADING_TOKEN_FIXES = {"|": "1", "I": "1", "l": "1"}

STEP_MARKER_RE = re.compile(r"^\d+[\.\)]\s*")

TRAILING_NOTE_RE = re.compile(r"^note[:\s]", re.IGNORECASE)

def segment_lines(text: str) -> tuple[list[str], list[str]]:
    section = "before"
    ingredient_lines: list[str] = []
    raw_step_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if INGREDIENTS_HEADER_RE.match(line):
            section = "ingredients"
            continue
        if DIRECTIONS_HEADER_RE.match(line):
            section = "steps"
            continue
        if TRAILING_NOTE_RE.match(line):
            section = "done"
            continue

        if section == "ingredients":
            ingredient_lines.append(line)
        elif section == "steps":
            raw_step_lines.append(line)

    # Rejoin wrapped lines: a new step starts only at a numbered marker;
    # everything else is a continuation of the previous step.
    steps: list[str] = []
    for line in raw_step_lines:
        if STEP_MARKER_RE.match(line) or not steps:
            steps.append(line)
        else:
            steps[-1] = f"{steps[-1]} {line}"

    return ingredient_lines, steps

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
        if re.match(r"^\d", token):
            break
        if token in LEADING_TOKEN_FIXES:
            tokens[start] = LEADING_TOKEN_FIXES[token]
            break
        if len(token) <= 1:
            start += 1
            continue
        break
    return " ".join(tokens[start:])


def _parse_quantity(token: str) -> float:
    token = token.strip()
    if "-" in token and "/" not in token:
        low, high = token.split("-")
        return (float(low) + float(high)) / 2
    if " " in token and "/" in token:
        whole, frac = token.split(" ", 1)
        num, denom = frac.split("/")
        return float(whole) + float(num) / float(denom)
    if "/" in token:
        num, denom = token.split("/")
        return float(num) / float(denom)
    return float(token)


def parse_ingredient_line(line: str) -> dict:
    line = _strip_leading_noise_tokens(line)

    match = QUANTITY_RE.match(line)
    quantity = None
    is_range = False
    rest = line
    if match:
        raw_qty = match.group(1)
        is_range = "-" in raw_qty and "/" not in raw_qty
        quantity = _parse_quantity(raw_qty)
        rest = line[match.end():].strip()

    words = rest.split()
    unit = None
    if words and words[0].lower().rstrip(".,") in UNIT_WORDS:
        unit = words[0].lower().rstrip(".,")
        if unit in {"lb", "ib", "lbs", "ibs"}:
            unit = "lb"
        rest = " ".join(words[1:])

    result = {"quantity": quantity, "unit": unit, "raw_name": rest.strip()}
    if is_range:
        result["ambiguous_quantity"] = True
    return result