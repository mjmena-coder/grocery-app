import io
import os
from PIL import Image
import pillow_heif

# Register HEIF opener with PIL so it supports HEIC/HEIF format
pillow_heif.register_heif_opener()


def process_uploaded_image_bytes(image_bytes: bytes, original_filename: str) -> tuple[bytes, str]:
    """
    Takes raw image bytes and original filename.
    If the image is HEIC/HEIF format, converts it to JPEG.
    Returns (processed_bytes, file_extension).
    """
    ext = os.path.splitext(original_filename)[1].lower() or ".jpg"

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        if pil_img.format in ("HEIF", "HEIC") or ext in (".heic", ".heif"):
            output = io.BytesIO()
            pil_img.convert("RGB").save(output, format="JPEG")
            return output.getvalue(), ".jpg"
    except Exception:
        pass

    return image_bytes, ext
