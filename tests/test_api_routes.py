from unittest.mock import patch
import io
from backend.models import Recipe


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_unlinked_canonical_ingredients(client):
    response = client.get("/canonical-ingredients/unlinked")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_generate_grocery_list_endpoint(client):
    response = client.post("/grocery-list/generate", json={"recipe_ids": []})
    assert response.status_code == 200
    assert "items" in response.json()


def test_list_stores_endpoint(client):
    response = client.get("/stores/")
    assert response.status_code == 200
    assert "stores" in response.json()


def test_upload_recipe_image_endpoint(client, session):
    recipe = Recipe(title="Test Recipe")
    session.add(recipe)
    session.commit()

    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    files = {"image": ("test_photo.heic", io.BytesIO(fake_image_bytes), "image/heic")}

    with patch("backend.api.routes.recipes.process_uploaded_image_bytes") as mock_process:
        mock_process.return_value = (b"converted_jpeg_bytes", ".jpg")

        response = client.post(f"/recipes/{recipe.id}/image", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["recipe_id"] == recipe.id
        assert data["image_url"].endswith(".jpg")
        mock_process.assert_called_once()
