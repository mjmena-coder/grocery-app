import io
import pytest
from PIL import Image
from backend.utils.image import process_uploaded_image_bytes


def _create_mock_jpeg_bytes() -> bytes:
    """Helper to generate valid JPEG image bytes in memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="red")
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_process_uploaded_image_bytes_passthrough_jpeg():
    """Non-HEIC images (like JPEG) should pass through unchanged."""
    raw_bytes = _create_mock_jpeg_bytes()
    filename = "test_recipe.jpg"

    processed_bytes, ext = process_uploaded_image_bytes(raw_bytes, filename)

    assert processed_bytes == raw_bytes
    assert ext == ".jpg"


def test_process_uploaded_image_bytes_heic_extension_conversion():
    """An image with a .heic extension should be converted to JPEG bytes and .jpg extension."""
    raw_bytes = _create_mock_jpeg_bytes()
    filename = "photo.heic"

    processed_bytes, ext = process_uploaded_image_bytes(raw_bytes, filename)

    assert ext == ".jpg"
    # Verify returned bytes form a valid PIL Image
    img = Image.open(io.BytesIO(processed_bytes))
    assert img.format == "JPEG"


def test_process_uploaded_image_bytes_fallback_on_corrupt_bytes():
    """Corrupt bytes should safely fall back to returning raw bytes and original extension."""
    corrupt_bytes = b"not_an_image_data"
    filename = "file.png"

    processed_bytes, ext = process_uploaded_image_bytes(corrupt_bytes, filename)

    assert processed_bytes == corrupt_bytes
    assert ext == ".png"
