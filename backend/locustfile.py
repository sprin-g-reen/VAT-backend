from locust import task, between, constant
from locust.contrib.fasthttp import FastHttpUser
import random


class AdminOptimizedUser(FastHttpUser):
    # Reduced wait time to increase throughput
    wait_time = constant(0)

    token = None
    category_ids = []

    def on_start(self):
        # 🔐 LOGIN
        res = self.client.post("/admin/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })

        if res.status_code != 200:
            return

        data = res.json()
        # Handle different response structures
        self.token = data.get("access_token") or data.get("data", {}).get("access_token")

        if not self.token:
            return

        # ✅ Apply token
        self.client.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    # =====================================================
    # 📂 CATEGORY OPERATIONS
    # =====================================================

    @task(2)
    def list_categories(self):
        with self.client.get("/admin/category/all?limit=50", catch_response=True) as res:
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
            catch_response=True
        ) as res:
            if res.status_code in [200, 201]:
                data = res.json()
                cid = data.get("_id") or data.get("data", {}).get("_id")
                if cid:
                    self.category_ids.append(cid)
            else:
                res.failure(f"Create Category Failed: {res.status_code}")

    # =====================================================
    # 📦 PRODUCT OPERATIONS
    # =====================================================

    @task(5)
    def list_products(self):
        with self.client.get("/admin/product/all?limit=50", catch_response=True) as res:
            if res.status_code != 200:
                res.failure(f"List Products Failed: {res.status_code}")

    @task(2)
    def create_product(self):
        if not self.category_ids:
            return

        payload = {
            "product_name": f"prod_{random.getrandbits(32)}",
            "description": "Optimized performance test product",
            "price": random.randint(10, 1000),
            "category_id": random.choice(self.category_ids),
            "subcategory_id": "SUB001" # Assuming a default subcategory exists
        }

        with self.client.post(
            "/admin/product/create",
            json=payload,
            catch_response=True
        ) as res:
            if res.status_code not in [200, 201]:
                res.failure(f"Create Product Failed: {res.status_code}")