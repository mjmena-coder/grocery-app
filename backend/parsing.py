import re

from PIL import Image
import pytesseract


UNIT_WORDS = {
    "cup", "cups", "tbsp", "tablespoon", "tablespoons",
    "tsp", "teaspoon", "teaspoons", "oz", "ounce", "ounces",
    "lb", "lbs", "pound", "pounds", "g", "gram", "grams",
    "kg", "ml", "l", "liter", "liters", "pinch", "clove", "cloves",
    "can", "cans",
}

QUANTITY_RE = re.compile(r"^\s*(\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+)\s*")


def ocr_image(path: str) -> str:
    """Extract raw text from a photographed recipe page."""
    image = Image.open(path)
    return pytesseract.image_to_string(image)


def segment_lines(text: str) -> tuple[list[str], list[str]]:
    """
    Crude split: lines that start with a digit are treated as
    ingredients, everything else as steps. Deliberately naive --
    this is the walking-skeleton version, refined once real OCR
    output has actually been seen.
    """
    ingredient_lines = []
    step_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^\d", line):
            ingredient_lines.append(line)
        else:
            step_lines.append(line)
    return ingredient_lines, step_lines


def _parse_quantity(token: str) -> float:
    token = token.strip()
    if " " in token and "/" in token:
        whole, frac = token.split(" ", 1)
        num, denom = frac.split("/")
        return float(whole) + float(num) / float(denom)
    if "/" in token:
        num, denom = token.split("/")
        return float(num) / float(denom)
    return float(token)


def parse_ingredient_line(line: str) -> dict:
    """
    Crude, deterministic ingredient-line parser: quantity, unit, name.
    Not meant to be perfect yet -- just structured enough to save to
    the schema and prove the pipeline end to end. Deepened later.
    """
    line = line.strip()
    match = QUANTITY_RE.match(line)
    quantity = None
    rest = line
    if match:
        quantity = _parse_quantity(match.group(1))
        rest = line[match.end():].strip()

    words = rest.split()
    unit = None
    if words and words[0].lower().rstrip(".,") in UNIT_WORDS:
        unit = words[0].lower().rstrip(".,")
        rest = " ".join(words[1:])

    return {"quantity": quantity, "unit": unit, "raw_name": rest.strip()}