import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def get_auth_header():
    # Signup
    email = "test@example.com"
    password = "Password123!"
    client.post("/auth/signup", json={
        "name": "Test User",
        "phone": "1234567890",
        "email": email,
        "password": password
    })
    # Signin
    res = client.post("/auth/signin", json={
        "identifier": email,
        "password": password
    })
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Auth service running"}

def test_category_crud():
    headers = get_auth_header()
    # Create
    response = client.post("/category/create", json={"category_name": "Electronics"}, headers=headers)
    assert response.status_code == 201
    category_id = response.json()["data"]["_id"]

    # Get all (with pagination)
    response = client.get("/category/all?skip=0&limit=5")
    assert response.status_code == 200
    assert any(c["_id"] == category_id for c in response.json()["data"])

    # Get single
    response = client.get(f"/category/{category_id}")
    assert response.status_code == 200
    assert response.json()["data"]["category_name"] == "Electronics"

    # Update
    response = client.put(f"/category/update/{category_id}", json={"category_name": "Tech"}, headers=headers)
    assert response.status_code == 200

    response = client.get(f"/category/{category_id}")
    assert response.json()["data"]["category_name"] == "Tech"

    # Delete
    response = client.delete(f"/category/delete/{category_id}", headers=headers)
    assert response.status_code == 200

    response = client.get(f"/category/{category_id}")
    assert response.status_code == 404

def test_subcategory_crud():
    headers = get_auth_header()
    # Create category first
    res_cat = client.post("/category/create", json={"category_name": "Electronics"}, headers=headers)
    cat_id = res_cat.json()["data"]["_id"]

    # Create subcategory
    response = client.post("/subcategory/create", json={
        "subcategory_name": "Phones",
        "category_id": cat_id
    }, headers=headers)
    assert response.status_code == 201
    sub_id = response.json()["data"]["_id"]

    # Get single
    response = client.get(f"/subcategory/{sub_id}")
    assert response.status_code == 200
    assert response.json()["data"]["subcategory_name"] == "Phones"

    # Update
    response = client.put(f"/subcategory/update/{sub_id}", json={"subcategory_name": "Smartphones"}, headers=headers)
    assert response.status_code == 200

    # Delete
    response = client.delete(f"/subcategory/delete/{sub_id}", headers=headers)
    assert response.status_code == 200
