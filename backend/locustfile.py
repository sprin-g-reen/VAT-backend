from locust import task, constant
from locust.contrib.fasthttp import FastHttpUser
import random
import logging
from gevent.lock import Semaphore

# Configure logging for locust
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("locust-test")

login_lock = Semaphore()

class AdminOptimizedUser(FastHttpUser):
    wait_time = constant(0)

    token = None  # shared token

    def on_start(self):
        self.category_ids = []
        self.auth_headers = {}
        self.ensure_logged_in()

    def ensure_logged_in(self):
        if not AdminOptimizedUser.token:
            with login_lock:
                # Double check inside lock
                if not AdminOptimizedUser.token:
                    with self.client.post(
                        "/admin/auth/login",
                        json={
                            "email": "admin@test.com",
                            "password": "admin123"
                        },
                        name="/admin/auth/login"
                    ) as res:
                        if res.status_code != 200:
                            logger.error(f"LOGIN FAILED: {res.status_code} - {res.text}")
                            return

                        data = res.json()
                        AdminOptimizedUser.token = (
                            data.get("access_token") or data.get("data", {}).get("access_token")
                        )

        if AdminOptimizedUser.token:
            self.auth_headers = {
                "Authorization": f"Bearer {AdminOptimizedUser.token}",
                "Content-Type": "application/json"
            }

    @task(1)
    def login_performance_test(self):
        """Dedicated task to monitor login performance independently"""
        with self.client.post(
            "/admin/auth/login",
            json={
                "email": "admin@test.com",
                "password": "admin123"
            },
            name="/admin/auth/login"
        ) as res:
            if res.status_code != 200:
                res.failure(f"Login failed: {res.text}")

    # ---------------- CATEGORY ---------------- #

    @task(2)
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
                try:
                    data = res.json()
                    cid = data.get("data", {}).get("_id") or data.get("_id")
                    if cid:
                        self.category_ids.append(cid)
                except:
                    res.failure("Invalid JSON")
            else:
                logger.error(f"CATEGORY ERROR: {res.status_code} - {res.text}")
                res.failure(res.text)

    # ---------------- PRODUCT ---------------- #

    @task(3)
    def create_product(self):
        if not self.category_ids:
            return

        payload = {
            "product_name": f"prod_{random.getrandbits(32)}",
            "description": "load test product",
            "price": random.randint(10, 1000),
            "category_id": random.choice(self.category_ids)
        }

        with self.client.post(
            "/admin/product/create",
            json=payload,
            headers=self.auth_headers,
            catch_response=True
        ) as res:

            if res.status_code not in [200, 201]:
                logger.error(f"PRODUCT ERROR: {res.status_code} - {res.text}")
                res.failure(res.text)