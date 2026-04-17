import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Auth service running 🚀"}

def test_category_crud():
    # Create
    response = client.post("/category/create", json={"category_name": "Electronics"})
    assert response.status_code == 201
    category_id = response.json()["data"]["_id"]

    # Get all
    response = client.get("/category/all")
    assert response.status_code == 200
    assert any(c["_id"] == category_id for c in response.json()["data"])

    # Get single
    response = client.get(f"/category/{category_id}")
    assert response.status_code == 200
    assert response.json()["data"]["category_name"] == "Electronics"

    # Update
    response = client.put(f"/category/update/{category_id}", json={"category_name": "Tech"})
    assert response.status_code == 200

    response = client.get(f"/category/{category_id}")
    assert response.json()["data"]["category_name"] == "Tech"

    # Delete
    response = client.delete(f"/category/delete/{category_id}")
    assert response.status_code == 200

    response = client.get(f"/category/{category_id}")
    assert response.status_code == 404

def test_subcategory_crud():
    # Create category first
    res_cat = client.post("/category/create", json={"category_name": "Electronics"})
    cat_id = res_cat.json()["data"]["_id"]

    # Create subcategory
    response = client.post("/subcategory/create", json={
        "subcategory_name": "Phones",
        "category_id": cat_id
    })
    assert response.status_code == 201
    sub_id = response.json()["data"]["_id"]

    # Get single
    response = client.get(f"/subcategory/{sub_id}")
    assert response.status_code == 200
    assert response.json()["data"]["subcategory_name"] == "Phones"

    # Update
    response = client.put(f"/subcategory/update/{sub_id}", json={"subcategory_name": "Smartphones"})
    assert response.status_code == 200

    # Delete
    response = client.delete(f"/subcategory/delete/{sub_id}")
    assert response.status_code == 200
