import asyncio
import os
import uuid
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load env variables
env_path = r"C:\Users\Admin\Vijay Angenya traders full\VAT-backend\backend\.env"
load_dotenv(env_path)

mongo_uri = os.getenv("MONGO_URI")
print(f"Seeding database at: {mongo_uri}")

async def seed_data():
    client = AsyncIOMotorClient(mongo_uri)
    try:
        db = client["ecommerce"]
        
        # Clear collections first
        await db.products.delete_many({})
        await db.categories.delete_many({})
        await db.subcategories.delete_many({})
        await db.counters.delete_many({})
        
        print("Cleared products, categories, subcategories, and counters collections.")
        
        # Initialize counters
        counters = [
            {"_id": "product_id", "seq": 0},
            {"_id": "category_id", "seq": 0},
            {"_id": "subcategory_id", "seq": 0},
            {"_id": "user_id", "seq": 1},  # admin is already created
            {"_id": "order_id", "seq": 0},
            {"_id": "payment_id", "seq": 0},
            {"_id": "return_id", "seq": 0},
            {"_id": "review_id", "seq": 0}
        ]
        await db.counters.insert_many(counters)
        print("Initialized counters.")

        # Create Categories
        categories_data = [
            {"name": "Beverages", "subcats": ["Coffee & Tea", "Juices & Sodas"]},
            {"name": "Dairy & Bread", "subcats": ["Milk & Butter", "Bread & Bakery"]},
            {"name": "Fruits & Vegetables", "subcats": ["Fresh Fruits", "Fresh Vegetables"]},
            {"name": "Snacks & Munchies", "subcats": ["Chips & Crisps", "Chocolates & Cookies"]},
            {"name": "Meat & Seafood", "subcats": ["Poultry & Meat", "Fish & Seafood"]}
        ]
        
        seeded_categories = {}
        seeded_subcategories = {}
        
        for index, cat in enumerate(categories_data):
            cat_id = f"CAT{index+1:06d}"
            cat_doc = {
                "_id": cat_id,
                "category_name": cat["name"],
                "is_active": True
            }
            await db.categories.insert_one(cat_doc)
            seeded_categories[cat["name"]] = cat_id
            print(f"Created category: {cat['name']} (ID: {cat_id})")
            
            for s_idx, sub in enumerate(cat["subcats"]):
                sub_id = f"SUB{index+1:02d}{s_idx+1:04d}"
                sub_doc = {
                    "_id": sub_id,
                    "subcategory_name": sub,
                    "category_id": cat_id,
                    "is_active": True
                }
                await db.subcategories.insert_one(sub_doc)
                seeded_subcategories[sub] = sub_id
                print(f"  Created subcategory: {sub} (ID: {sub_id})")

        # Create Products
        products_data = [
            {
                "product_name": "Foster Farms Breast Nuggets Shaped Chicken",
                "description": "Crispy and delicious chicken nuggets made from 100% white breast meat chicken.",
                "price": 399.00,
                "category": "Meat & Seafood",
                "subcategory": "Poultry & Meat",
                "image": "assets/images/grocery/01.jpg",
                "variants": [
                    {"sku": "CHKN-NUG-500G", "size": "500g", "color": "Golden", "product_variants_price": 399.00, "stock_quantity": 50},
                    {"sku": "CHKN-NUG-1KG", "size": "1kg", "color": "Golden", "product_variants_price": 749.00, "stock_quantity": 30}
                ]
            },
            {
                "product_name": "Lay's Potato Chips, Sweet Southern Heat BBQ",
                "description": "Lay's Kettle Cooked Potato Chips Sweet Southern Heat BBQ chips are seasoned with bbq flavor, with a touch of sweet heat.",
                "price": 120.00,
                "category": "Snacks & Munchies",
                "subcategory": "Chips & Crisps",
                "image": "assets/images/grocery/02.jpg",
                "variants": [
                    {"sku": "LAYS-BBQ-150G", "size": "150g", "color": "Red", "product_variants_price": 120.00, "stock_quantity": 100}
                ]
            },
            {
                "product_name": "Fresh Organic Bananas (Pack of 6)",
                "description": "Rich in potassium and vitamins, organically grown sweet yellow bananas.",
                "price": 89.00,
                "category": "Fruits & Vegetables",
                "subcategory": "Fresh Fruits",
                "image": "assets/images/grocery/03.jpg",
                "variants": [
                    {"sku": "BAN-ORG-6PCS", "size": "6 pcs", "color": "Yellow", "product_variants_price": 89.00, "stock_quantity": 40}
                ]
            },
            {
                "product_name": "Pastine Mellin Filid Angelo Tenero",
                "description": "Pastine Mellin Filid Angelo is made from 100% soft wheat flour, ideal for weaning babies.",
                "price": 249.00,
                "category": "Snacks & Munchies",
                "subcategory": "Chocolates & Cookies",
                "image": "assets/images/grocery/04.jpg",
                "variants": [
                    {"sku": "MEL-PAST-350G", "size": "350g", "color": "White", "product_variants_price": 249.00, "stock_quantity": 60}
                ]
            },
            {
                "product_name": "Organic Whole Milk (1 Gallon)",
                "description": "High-quality pasteurized organic whole milk containing essential nutrients.",
                "price": 299.00,
                "category": "Dairy & Bread",
                "subcategory": "Milk & Butter",
                "image": "assets/images/grocery/05.jpg",
                "variants": [
                    {"sku": "MILK-ORG-1GAL", "size": "1 Gal", "color": "White", "product_variants_price": 299.00, "stock_quantity": 25}
                ]
            },
            {
                "product_name": "Sliced Whole Wheat Bread",
                "description": "Soft and healthy whole wheat bread slices, baked fresh daily.",
                "price": 60.00,
                "category": "Dairy & Bread",
                "subcategory": "Bread & Bakery",
                "image": "assets/images/grocery/06.jpg",
                "variants": [
                    {"sku": "BREAD-WHT-400G", "size": "400g", "color": "Brown", "product_variants_price": 60.00, "stock_quantity": 80}
                ]
            },
            {
                "product_name": "Coca-Cola Classic Soda (Pack of 6)",
                "description": "The original crisp and refreshing taste of Coca-Cola in 330ml cans.",
                "price": 180.00,
                "category": "Beverages",
                "subcategory": "Juices & Sodas",
                "image": "assets/images/grocery/07.jpg",
                "variants": [
                    {"sku": "COKE-CLA-6CAN", "size": "6 Pack", "color": "Red", "product_variants_price": 180.00, "stock_quantity": 120}
                ]
            },
            {
                "product_name": "Premium French Roast Ground Coffee",
                "description": "Dark roast ground coffee with a bold, smoky flavor profile.",
                "price": 450.00,
                "category": "Beverages",
                "subcategory": "Coffee & Tea",
                "image": "assets/images/grocery/08.jpg",
                "variants": [
                    {"sku": "COFF-FR-250G", "size": "250g", "color": "Black", "product_variants_price": 450.00, "stock_quantity": 45}
                ]
            },
            {
                "product_name": "Organic Red Tomatoes (1kg)",
                "description": "Juicy and ripe organic red vine tomatoes.",
                "price": 120.00,
                "category": "Fruits & Vegetables",
                "subcategory": "Fresh Vegetables",
                "image": "assets/images/grocery/09.jpg",
                "variants": [
                    {"sku": "TOM-ORG-1KG", "size": "1kg", "color": "Red", "product_variants_price": 120.00, "stock_quantity": 50}
                ]
            },
            {
                "product_name": "Fresh Atlantic Salmon Fillet",
                "description": "Rich in Omega-3 fatty acids, fresh wild-caught Atlantic salmon fillet.",
                "price": 899.00,
                "category": "Meat & Seafood",
                "subcategory": "Fish & Seafood",
                "image": "assets/images/grocery/10.jpg",
                "variants": [
                    {"sku": "SALM-FIL-300G", "size": "300g", "color": "Pink", "product_variants_price": 899.00, "stock_quantity": 20}
                ]
            }
        ]

        for p_idx, prod in enumerate(products_data):
            p_id = f"PRD{p_idx+1:06d}"
            cat_name = prod["category"]
            subcat_name = prod["subcategory"]
            
            cat_id = seeded_categories.get(cat_name)
            subcat_id = seeded_subcategories.get(subcat_name)
            
            prod_doc = {
                "_id": p_id,
                "product_name": prod["product_name"],
                "description": prod["description"],
                "price": prod["price"],
                "category_id": cat_id,
                "subcategory_id": subcat_id,
                "product_is_active": True,
                "main_image": prod["image"],
                "images": [{"image_url": prod["image"]}],
                "additional_images": [],
                "variants": prod["variants"]
            }
            await db.products.insert_one(prod_doc)
            print(f"Created product: {prod['product_name']} (ID: {p_id})")
            
        # Update counters matching the seeded counts
        await db.counters.update_one({"_id": "category_id"}, {"$set": {"seq": len(categories_data)}})
        await db.counters.update_one({"_id": "subcategory_id"}, {"$set": {"seq": len(seeded_subcategories)}})
        await db.counters.update_one({"_id": "product_id"}, {"$set": {"seq": len(products_data)}})
        print("Updated counters sequences to match seeded items.")
        print("Successfully seeded grocery store data!")
        
    except Exception as e:
        print(f"Error seeding grocery data: {e}")

if __name__ == "__main__":
    asyncio.run(seed_data())
