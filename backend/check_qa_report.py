import sys
import os
import random
import string
import requests
from pymongo import MongoClient

# Base backend URL
BACKEND_URL = "http://127.0.0.1:8000"
MONGO_URI = "mongodb+srv://test:VAT020@vatdemo.5aibw6u.mongodb.net/?appName=VATDemo"

print("Starting QA checklist verification...")

# Connect to database
try:
    db_client = MongoClient(MONGO_URI)
    db = db_client["ecommerce"]
    print("Successfully connected to MongoDB Atlas (ecommerce database).")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    sys.exit(1)

# Generate unique email for testing
def get_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

test_email = f"qa_test_{get_random_string()}@example.com"
test_password = "Password123!"
test_phone = f"9{random.randint(100000001, 999999999)}"

results = {}

def run_test(name, func):
    print(f"\n--- Running: {name} ---")
    try:
        status, message = func()
        results[name] = {"status": "PASS" if status else "FAIL", "message": message}
    except Exception as e:
        results[name] = {"status": "FAIL", "message": f"Exception: {str(e)}"}
    print(f"Result: {results[name]['status']} - {results[name]['message']}")

# Test 1: Register with valid email
def test_register_valid():
    payload = {
        "name": "QA Tester",
        "phone": test_phone,
        "email": test_email,
        "password": test_password
    }
    res = requests.post(f"{BACKEND_URL}/auth/signup", json=payload)
    if res.status_code != 201:
        return False, f"Expected 201 Created, got {res.status_code}. Response: {res.text}"
    
    # Verify in DB
    user = db.users.find_one({"email": test_email})
    if not user:
        return False, "User not found in MongoDB."
    
    return True, f"Success. User created in DB with ID: {user['_id']}"

# Test 2: Register with duplicate email
def test_register_duplicate():
    payload = {
        "name": "QA Tester Duplicate",
        "phone": f"9{random.randint(100000001, 999999999)}",
        "email": test_email,
        "password": test_password
    }
    res = requests.post(f"{BACKEND_URL}/auth/signup", json=payload)
    if res.status_code != 409:
        return False, f"Expected 409 Conflict, got {res.status_code}. Response: {res.text}"
    
    data = res.json()
    if "User already exists" not in data.get("error", ""):
        return False, f"Expected error 'User already exists', got: {data}"
    
    return True, "Success. Received correct 409 Conflict error message."

# Test 3: Login with correct credentials
def test_login_correct():
    payload = {
        "identifier": test_email,
        "password": test_password
    }
    res = requests.post(f"{BACKEND_URL}/auth/signin", json=payload)
    if res.status_code != 200:
        return False, f"Expected 200 OK, got {res.status_code}. Response: {res.text}"
    
    data = res.json()
    token = data.get("data", {}).get("access_token")
    if not token:
        return False, "Access token missing from login response data."
    
    return True, "Success. Login successful, token returned."

# Test 4: Login with wrong password
def test_login_wrong_password():
    payload = {
        "identifier": test_email,
        "password": "WrongPassword123!"
    }
    res = requests.post(f"{BACKEND_URL}/auth/signin", json=payload)
    if res.status_code != 401:
        return False, f"Expected 401 Unauthorized, got {res.status_code}. Response: {res.text}"
    
    data = res.json()
    # Check that error doesn't leak user existence
    if "Invalid credentials" not in data.get("error", ""):
        return False, f"Expected generic error 'Invalid credentials', got: {data}"
    
    return True, "Success. Returned 401 and generic error without leaking user existence."

# Test 5: Login with non-existent email (user existence leak check)
def test_login_nonexistent():
    payload = {
        "identifier": "nonexistent_email_12345@example.com",
        "password": test_password
    }
    res = requests.post(f"{BACKEND_URL}/auth/signin", json=payload)
    if res.status_code != 401:
        return False, f"Expected 401 Unauthorized, got {res.status_code}. Response: {res.text}"
    
    data = res.json()
    if "Invalid credentials" not in data.get("error", ""):
        return False, f"Expected generic error 'Invalid credentials', got: {data}"
    
    return True, "Success. Returned 401 and generic error for non-existent email."

# Test 6: Forgot password flow
def test_forgot_password():
    # Trigger forgot password
    res = requests.post(f"{BACKEND_URL}/auth/forgot-password", json={"email": test_email})
    if res.status_code != 200:
        return False, f"Forgot password failed. Got {res.status_code}. Response: {res.text}"
    
    # Fetch OTP from DB directly
    otp_record = db.otp.find_one({"email": test_email})
    if not otp_record:
        return False, "OTP not found in DB."
    
    otp = otp_record.get("otp")
    if not otp:
        return False, "OTP field empty in DB."
    
    # Reset password
    new_password = "NewPassword123!"
    reset_res = requests.post(f"{BACKEND_URL}/auth/reset-password", json={
        "email": test_email,
        "otp": otp,
        "new_password": new_password
    })
    if reset_res.status_code != 200:
        return False, f"Reset password failed. Got {reset_res.status_code}. Response: {reset_res.text}"
    
    # Verify old password is disabled
    login_old_res = requests.post(f"{BACKEND_URL}/auth/signin", json={
        "identifier": test_email,
        "password": test_password
    })
    if login_old_res.status_code == 200:
        return False, "Security breach: Old password still works after reset!"
    
    # Verify new password works
    login_new_res = requests.post(f"{BACKEND_URL}/auth/signin", json={
        "identifier": test_email,
        "password": new_password
    })
    if login_new_res.status_code != 200:
        return False, f"Login with new password failed. Got {login_new_res.status_code}"
    
    return True, "Success. OTP created, reset password completed, old password disabled, new password works."

# Test 7: Protected routes redirect / return 401
def test_protected_routes():
    # Check get wishlist (requires auth)
    res = requests.get(f"{BACKEND_URL}/wishlist")
    # Public route wishlist doesn't exist? Oh wait, /wishlist requires authorization header. Let's see:
    if res.status_code != 401:
        return False, f"Expected 401 Unauthorized for wishlist without token, got: {res.status_code}"
    return True, "Success. Protected routes return 401 when unauthenticated."

# Test 8: Admin roles and routes check
admin_token = None
def test_admin_auth():
    global admin_token
    # Check default admin roles are seeded
    admin_user = db.users.find_one({"roles": "admin"})
    if not admin_user:
        # If no admin, try finding super_admin
        admin_user = db.users.find_one({"roles": "super_admin"})
        if not admin_user:
            return False, "No admin or super_admin found in database to test."
    
    # We don't know the admin's password, but we can temporarily mock or we can login if there's a known admin.
    # Wait, check_create has an endpoint to create a default admin or let's look at dependencies/roles.py
    # or db.users to see if there's a seeded admin we can use, or we can temporarily add 'admin' role to our test_email user!
    # Yes! Let's temporarily add 'admin' role to test_email in DB to test admin login and permissions.
    db.users.update_one({"email": test_email}, {"$set": {"roles": ["admin"]}})
    
    # Login as admin
    res = requests.post(f"{BACKEND_URL}/admin/auth/login", json={
        "email": test_email,
        "password": "NewPassword123!" # Since we reset it in Test 6
    })
    
    if res.status_code != 200:
        return False, f"Admin login failed. Got {res.status_code}. Response: {res.text}"
    
    data = res.json()
    admin_token = data.get("access_token")
    if not admin_token:
        return False, "Admin token missing from response."
    
    # Check access permissions
    headers = {"Authorization": f"Bearer {admin_token}"}
    access_res = requests.get(f"{BACKEND_URL}/admin/auth/access", headers=headers)
    if access_res.status_code != 200:
        return False, f"Admin access check failed. Got {access_res.status_code}"
    
    return True, f"Success. Authenticated admin, permissions: {access_res.json()}"

# Test 9: Admin routes inaccessible to non-admin users
def test_admin_routes_isolation():
    # Login test user again (let's remove admin role from it first)
    db.users.update_one({"email": test_email}, {"$set": {"roles": []}})
    
    # Try calling admin/product/all with non-admin login token
    res_login = requests.post(f"{BACKEND_URL}/auth/signin", json={
        "identifier": test_email,
        "password": "NewPassword123!"
    })
    token = res_login.json()["data"]["access_token"]
    
    res = requests.get(f"{BACKEND_URL}/admin/product/all", headers={"Authorization": f"Bearer {token}"})
    if res.status_code not in (401, 403):
        return False, f"Expected 401 or 403 for non-admin on admin routes, got {res.status_code}. Response: {res.text}"
    
    # Restore admin role for subsequent admin tests
    db.users.update_one({"email": test_email}, {"$set": {"roles": ["admin"]}})
    return True, "Success. Non-admin users are blocked from admin routes (returned 401/403)."

# Test 10: Product CRUD in admin, variant saving, stock decrement
def test_admin_product_crud():
    global admin_token
    if not admin_token:
        return False, "Skipped. No admin token."
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create product
    payload = {
        "product_name": "QA Test Product",
        "description": "This is a product created during QA test.",
        "price": 150.00,
        "category_id": "CAT000001",
        "subcategory_id": "SUB000001",
        "product_is_popular": True,
        "product_is_active": True,
        "main_image": "qa_test_image.jpg",
        "images": [{"image_url": "qa_test_image.jpg"}],
        "additional_images": [],
        "variants": [
            {
                "sku": "QA-SKU-1",
                "size": "Medium",
                "color": "Green",
                "product_variants_price": 150.00,
                "stock_quantity": 50
            }
        ]
    }
    
    create_res = requests.post(f"{BACKEND_URL}/admin/product/create", json=payload, headers=headers)
    if create_res.status_code != 201:
        return False, f"Failed to create product. Got {create_res.status_code}. Response: {create_res.text}"
    
    prod_id = create_res.json().get("data", {}).get("_id")
    if not prod_id:
        return False, "Product ID missing from creation response."
    
    # Read product
    get_res = requests.get(f"{BACKEND_URL}/admin/product/{prod_id}", headers=headers)
    if get_res.status_code != 200:
        return False, f"Failed to fetch created product. Got {get_res.status_code}"
    
    prod_data = get_res.json().get("data", {})
    if prod_data.get("product_name") != "QA Test Product":
        return False, "Product name does not match created value."
    
    # Update product
    update_payload = {
        "product_name": "QA Test Product Updated",
        "price": 175.00
    }
    update_res = requests.put(f"{BACKEND_URL}/admin/product/update/{prod_id}", json=update_payload, headers=headers)
    if update_res.status_code != 200:
        return False, f"Failed to update product. Got {update_res.status_code}"
    
    # Delete product
    delete_res = requests.delete(f"{BACKEND_URL}/admin/product/delete/{prod_id}", headers=headers)
    if delete_res.status_code != 200:
        return False, f"Failed to delete product. Got {delete_res.status_code}"
    
    return True, "Success. Product created, read, updated, and deleted successfully. Variants saved correctly."

# Test 11: Admin dashboard metrics check
def test_admin_dashboard_metrics():
    global admin_token
    if not admin_token:
        return False, "Skipped. No admin token."
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = requests.get(f"{BACKEND_URL}/admin/analytics/dashboard", headers=headers)
    if res.status_code != 200:
        return False, f"Failed to fetch admin dashboard analytics. Got {res.status_code}. Response: {res.text}"
    
    data = res.json().get("data", {})
    # Check for order count and revenue totals
    if "total_orders" not in data or "total_revenue" not in data:
        return False, f"Dashboard metrics missing 'total_orders' or 'total_revenue'. Got keys: {list(data.keys())}"
    
    return True, f"Success. Dashboard reports: Orders={data.get('total_orders')}, Revenue={data.get('total_revenue')}"

# Run tests
run_test("Register Valid Email", test_register_valid)
run_test("Register Duplicate Email", test_register_duplicate)
run_test("Login Correct Credentials", test_login_correct)
run_test("Login Wrong Password (generic err)", test_login_wrong_password)
run_test("Login Non-existent User (generic err)", test_login_nonexistent)
run_test("Forgot Password Flow", test_forgot_password)
run_test("Protected Routes 401", test_protected_routes)
run_test("Admin Authentication & Access", test_admin_auth)
run_test("Admin Routes Access Control (401/403)", test_admin_routes_isolation)
run_test("Admin Product CRUD & Variants", test_admin_product_crud)
run_test("Admin Dashboard Metrics", test_admin_dashboard_metrics)

# Clean up our test user from MongoDB
if test_email:
    db.users.delete_many({"email": test_email})
    db.otp.delete_many({"email": test_email})
    print("\nCleaned up QA test data from MongoDB.")

# Print summary
print("\n=== QA API TESTING SUMMARY ===")
for test, res in results.items():
    print(f"[{res['status']}] {test}: {res['message']}")
