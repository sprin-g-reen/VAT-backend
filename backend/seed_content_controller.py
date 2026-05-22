import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime

async def seed_content_controller():
    load_dotenv('VAT-backend/backend/.env')
    uri = os.getenv('MONGO_URI')
    if not uri:
        print("MONGO_URI not found in .env")
        return
    
    client = AsyncIOMotorClient(uri)
    db = client.ecommerce
    
    # Define initial content
    initial_content = [
        # HEADER NAVIGATION
        {"section_name": "header", "content_key": "nav_all", "content_value": "ALL", "display_order": 1},
        {"section_name": "header", "content_key": "nav_beverages", "content_value": "BEVERAGES", "display_order": 2},
        {"section_name": "header", "content_key": "nav_dairy", "content_value": "DAIRY & BREAD", "display_order": 3},
        {"section_name": "header", "content_key": "nav_fruits", "content_value": "FRUITS & VEGETABLES", "display_order": 4},
        {"section_name": "header", "content_key": "nav_snacks", "content_value": "SNACKS & MUNCHIES", "display_order": 5},
        {"section_name": "header", "content_key": "nav_meat", "content_value": "MEAT & SEAFOOD", "display_order": 6},
        {"section_name": "header", "content_key": "nav_shop", "content_value": "SHOP", "display_order": 7},
        
        # FEATURED CATEGORIES
        {"section_name": "featured_categories", "content_key": "section_title", "content_value": "Featured Categories", "display_order": 0},
        {"section_name": "featured_categories", "content_key": "cat_beverages", "content_value": {"name": "Beverages", "img": "assets/images/category/01.jpg", "link": "shop-grid-sidebar.html?category=CAT000001", "count": "20 Items"}, "display_order": 1},
        {"section_name": "featured_categories", "content_key": "cat_dairy", "content_value": {"name": "Dairy & Bread", "img": "assets/images/category/02.jpg", "link": "shop-grid-sidebar.html?category=CAT000002", "count": "15 Items"}, "display_order": 2},
        {"section_name": "featured_categories", "content_key": "cat_fruits", "content_value": {"name": "Fruits & Vegetables", "img": "assets/images/category/03.jpg", "link": "shop-grid-sidebar.html?category=CAT000003", "count": "30 Items"}, "display_order": 3},
        {"section_name": "featured_categories", "content_key": "cat_snacks", "content_value": {"name": "Snacks & Munchies", "img": "assets/images/category/04.jpg", "link": "shop-grid-sidebar.html?category=CAT000004", "count": "25 Items"}, "display_order": 4},
        {"section_name": "featured_categories", "content_key": "cat_meat", "content_value": {"name": "Meat & Seafood", "img": "assets/images/category/05.jpg", "link": "shop-grid-sidebar.html?category=CAT000005", "count": "10 Items"}, "display_order": 5},
        
        # TRENDING SECTION
        {"section_name": "trending", "content_key": "section_title", "content_value": "Trending items", "display_order": 0},
        {"section_name": "trending", "content_key": "tab_fresh", "content_value": "Fresh Produce", "display_order": 1},
        {"section_name": "trending", "content_key": "tab_dairy", "content_value": "Dairy and Eggs", "display_order": 2},
        {"section_name": "trending", "content_key": "tab_meat", "content_value": "Meat and Seafood", "display_order": 3},
        {"section_name": "trending", "content_key": "tab_bakery", "content_value": "Bakery", "display_order": 4},
        {"section_name": "trending", "content_key": "tab_pantry", "content_value": "Pantry Staples", "display_order": 5},
        {"section_name": "trending", "content_key": "tab_snacks", "content_value": "Snacks and Confectionery", "display_order": 6},
        {"section_name": "trending", "content_key": "tab_frozen", "content_value": "Frozen Foods", "display_order": 7},
        {"section_name": "trending", "content_key": "tab_household", "content_value": "Household Cleaning", "display_order": 8},
        
        # FOOTER CONTENT
        {"section_name": "footer", "content_key": "company_desc", "content_value": "Vijay Anjenya Traders is your one-stop shop for all your grocery needs. We provide fresh produce, dairy, meat, and more at the best prices.", "display_order": 1},
        {"section_name": "footer", "content_key": "head_about", "content_value": "About Company", "display_order": 2},
        {"section_name": "footer", "content_key": "head_stores", "content_value": "Our Stores", "display_order": 3},
        {"section_name": "footer", "content_key": "head_categories", "content_value": "Shop Categories", "display_order": 4},
        {"section_name": "footer", "content_key": "head_links", "content_value": "Useful Links", "display_order": 5},
        {"section_name": "footer", "content_key": "copyright", "content_value": "Copyright 2026 ©Vijay Anjenya Traders. All rights reserved.", "display_order": 6},
        
        # GENERAL HOME TEXT
        {"section_name": "general", "content_key": "hero_pre_title", "content_value": "Get up to 30% off on your first ₹150 purchase", "display_order": 1},
        {"section_name": "general", "content_key": "hero_title", "content_value": "Do not miss our amazing grocery deals", "display_order": 2},
        {"section_name": "general", "content_key": "hero_desc", "content_value": "We have prepared special discounts for you on grocery products. Don't miss these opportunities...", "display_order": 3},
        {"section_name": "general", "content_key": "hero_btn", "content_value": "Shop Now", "display_order": 4},
    ]
    
    # Clear existing content
    await db.content_controller.delete_many({})
    
    # Insert new content
    for idx, item in enumerate(initial_content):
        item["_id"] = f"CONT{idx:04d}"
        item["is_active"] = True
        item["created_at"] = datetime.utcnow()
        item["updated_at"] = datetime.utcnow()
        await db.content_controller.insert_one(item)
        
    # Update admin permissions
    content_perms = ["view_content", "create_content", "update_content", "delete_content"]
    admin_role = await db.roles.find_one({"name": "admin"})
    if admin_role:
        current_perms = admin_role.get("permissions", [])
        if "*" not in current_perms:
            updated_perms = list(set(current_perms + content_perms))
            await db.roles.update_one({"name": "admin"}, {"$set": {"permissions": updated_perms}})
            
    print("Content controller seeded successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_content_controller())
