# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException
from utils.security import get_current_user
from db import db


from redis_db import redis_client
import json

DEFAULT_ADMIN_PERMISSIONS = {
    "view_dashboard",
    "view_product",
    "create_product",
    "update_product",
    "delete_product",
    "view_category",
    "create_category",
    "update_category",
    "delete_category",
    "view_order",
    "create_order",
    "update_order",
    "delete_order",
    "view_customer",
    "create_customer",
    "update_customer",
    "delete_customer",
    "view_banner",
    "create_banner",
    "update_banner",
    "delete_banner",
    "view_content",
    "create_content",
    "update_content",
    "delete_content",
    "view_offers",
    "view_reports",
    "view_settings",
    "view_applications",
    "view_docs",
    "create_admin_user",
    "create_role",
    "update_role",
    "view_review",
    "delete_review",
}

async def ensure_default_admin_roles():
    """Backfill reserved admin roles for installations created before RBAC."""
    await db.roles.update_one(
        {"name": "admin"},
        {
            "$setOnInsert": {"name": "admin"},
            "$addToSet": {"permissions": {"$each": sorted(DEFAULT_ADMIN_PERMISSIONS)}},
        },
        upsert=True,
    )

    super_admin_role = await db.roles.find_one({"name": "super_admin"}, {"permissions": 1})
    if not super_admin_role or "*" not in super_admin_role.get("permissions", []):
        await db.roles.update_one(
            {"name": "super_admin"},
            {"$set": {"name": "super_admin", "permissions": ["*"]}},
            upsert=True,
        )

    await redis_client.delete("role_perms:admin", "role_perms:super_admin")


async def get_permissions(user):
    user_roles = user.get("roles", [])
    if not user_roles:
        return set()

    permissions = set()
    roles_to_fetch = []

    for role in user_roles:
        cache_key = f"role_perms:{role}"
        cached = await redis_client.get(cache_key)
        if cached:
            perms = set(json.loads(cached))
            if "*" in perms:
                return {"*"}
            permissions.update(perms)
        else:
            roles_to_fetch.append(role)

    if roles_to_fetch:
        # Fetch missing roles from DB and cache them
        cursor = db.roles.find({"name": {"$in": roles_to_fetch}}, {"name": 1, "permissions": 1})
        async for role_doc in cursor:
            role_name = role_doc["name"]
            role_perms = role_doc.get("permissions", [])
            await redis_client.setex(f"role_perms:{role_name}", 3600, json.dumps(role_perms))

            perms_set = set(role_perms)
            if "*" in perms_set:
                return {"*"}
            permissions.update(perms_set)

    return permissions


def require_permission(permission: str):
    async def checker(user=Depends(get_current_user)):
        perms = await get_permissions(user)

        if "*" in perms or permission in perms:
            return user

        raise HTTPException(status_code=403, detail="Permission denied")

    return checker
