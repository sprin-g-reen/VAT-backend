from locust import HttpUser, task, between
import random


class AdminCreateUser(HttpUser):
    wait_time = between(1, 2)

    token = None
    category_ids = []

    def on_start(self):
        # 🔐 LOGIN
        res = self.client.post("/admin/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })

        if res.status_code != 200:
            print("❌ LOGIN FAILED:", res.text)
            return

        data = res.json()

        self.token = (
            data.get("data", {}).get("access_token")
            or data.get("access_token")
        )

        if not self.token:
            print("❌ TOKEN MISSING:", data)
            return

        # ✅ Apply token
        self.client.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    # =====================================================
    # 📂 CREATE CATEGORY
    # =====================================================

    @task(2)
    def create_category(self):
        payload = {
            "category_name": f"cat_{random.randint(1000,9999)}"
        }

        with self.client.post(
            "/admin/category/create",
            json=payload,
            catch_response=True
        ) as res:

            print("CATEGORY:", res.status_code, res.text)

            if res.status_code in [200, 201]:
                try:
                    data = res.json()
                    cid = data.get("data", {}).get("_id") or data.get("_id")

                    if cid:
                        self.category_ids.append(cid)
                except:
                    pass
            else:
                res.failure(res.text)

    # =====================================================
    # 📦 CREATE PRODUCT
    # =====================================================

    @task(3)
    def create_product(self):
        if not self.category_ids:
            return  # wait until category exists

        payload = {
            "product_name": f"prod_{random.randint(1000,9999)}",
            "description": "test product",
            "price": random.randint(100, 500),
            "category_id": random.choice(self.category_ids),
            "brand_id": "001"
        }

        with self.client.post(
            "/admin/product/create",
            json=payload,
            catch_response=True
        ) as res:

            print("PRODUCT:", res.status_code, res.text)

            if res.status_code not in [200, 201]:
                res.failure(res.text)