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