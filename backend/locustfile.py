from locust import task, between, constant
from locust.contrib.fasthttp import FastHttpUser
import random


class AdminOptimizedUser(FastHttpUser):
    # Reduced wait time to increase throughput
    wait_time = constant(0)

    auth_headers = {}
    category_ids = []
    subcategory_ids = []

    def on_start(self):
        # 🔐 LOGIN
        # Note: If this fails in local dev, ensure the admin user exists
        res = self.client.post("/admin/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })

        if res.status_code != 200:
            # Fallback to creating the admin if it doesn't exist (useful for clean envs)
            self.client.post("/admin/users/create", json={
                "email": "admin@test.com",
                "password": "admin123",
                "roles": ["admin", "create_category", "view_category", "create_product", "view_product"]
            })
            # Try login again
            res = self.client.post("/admin/auth/login", json={
                "email": "admin@test.com",
                "password": "admin123"
            })

        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token") or data.get("data", {}).get("access_token")
            if token:
                self.auth_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                # 📂 Initial data fetch to make subsequent tasks valid
                self._fetch_initial_data()

    def _fetch_initial_data(self):
        """Pre-populate IDs to ensure create tasks have valid references"""
        # Fetch categories
        res = self.client.get("/admin/category/all?limit=100", headers=self.auth_headers)
        if res.status_code == 200:
            data = res.json().get("data", [])
            self.category_ids = [c.get("_id") for c in data if c.get("_id")]

        # Fetch subcategories
        res = self.client.get("/subcategory/all?limit=100", headers=self.auth_headers)
        if res.status_code == 200:
            data = res.json().get("data", [])
            self.subcategory_ids = [s.get("_id") or s.get("id") for s in data]

        # If no subcategories exist, create one to ensure products can be created
        if not self.subcategory_ids and self.category_ids:
            res = self.client.post("/subcategory/create", json={
                "subcategory_name": "Default Test Subcategory",
                "category_id": self.category_ids[0]
            }, headers=self.auth_headers)
            if res.status_code in [200, 201]:
                sid = res.json().get("data", {}).get("_id")
                if sid:
                    self.subcategory_ids.append(sid)

    # =====================================================
    # 📂 CATEGORY OPERATIONS
    # =====================================================

    @task(2)
    def list_categories(self):
        with self.client.get("/admin/category/all?limit=50", headers=self.auth_headers, catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"List Categories Failed: {res.status_code}")

    @task(1)
    def create_category(self):
        payload = {
            "category_name": f"cat_{random.getrandbits(32)}"
        }

        with self.client.post(
            "/admin/category/create",
            json=payload,
            headers=self.auth_headers,
            catch_response=True
        ) as res:
            if res.status_code in [200, 201]:
                data = res.json()
                cid = data.get("_id") or data.get("data", {}).get("_id")
                if cid:
                    self.category_ids.append(cid)
                    # When a category is created, often a subcategory is needed for products
                    self._create_related_subcategory(cid)
            else:
                res.failure(f"Create Category Failed: {res.status_code}")

    def _create_related_subcategory(self, category_id):
        payload = {
            "subcategory_name": f"sub_{random.getrandbits(32)}",
            "category_id": category_id
        }
        res = self.client.post("/subcategory/create", json=payload, headers=self.auth_headers)
        if res.status_code in [200, 201]:
            sid = res.json().get("data", {}).get("_id")
            if sid:
                self.subcategory_ids.append(sid)

    # =====================================================
    # 📦 PRODUCT OPERATIONS
    # =====================================================

    @task(5)
    def list_products(self):
        with self.client.get("/admin/product/all?limit=50", headers=self.auth_headers, catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"List Products Failed: {res.status_code}")

    @task(2)
    def create_product(self):
        if not self.category_ids or not self.subcategory_ids:
            return

        payload = {
            "product_name": f"prod_{random.getrandbits(32)}",
            "description": "Optimized performance test product",
            "price": random.randint(10, 1000),
            "category_id": random.choice(self.category_ids),
            "subcategory_id": random.choice(self.subcategory_ids)
        }

        with self.client.post(
            "/admin/product/create",
            json=payload,
            headers=self.auth_headers,
            catch_response=True
        ) as res:
            if res.status_code not in [200, 201]:
                res.failure(f"Create Product Failed: {res.status_code}")
