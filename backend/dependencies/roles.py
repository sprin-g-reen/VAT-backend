from fastapi import Depends, HTTPException
from utils.security import get_current_user
from db import db


# In-memory cache for role permissions to minimize DB hits
ROLE_PERMISSIONS_CACHE = {}

async def get_permissions(user):
    user_roles = user.get("roles", [])
    if not user_roles:
        return set()

    permissions = set()

    # Identify roles not in cache
    roles_to_fetch = [r for r in user_roles if r not in ROLE_PERMISSIONS_CACHE]

    if roles_to_fetch:
        # Fetch all missing roles in a single query
        cursor = db.roles.find({"name": {"$in": roles_to_fetch}})
        async for role_doc in cursor:
            ROLE_PERMISSIONS_CACHE[role_doc["name"]] = set(role_doc.get("permissions", []))

    for role in user_roles:
        perms = ROLE_PERMISSIONS_CACHE.get(role, set())
        if "*" in perms:
            return {"*"}  # super admin
        permissions.update(perms)

    return permissions


def require_permission(permission: str):
    async def checker(user=Depends(get_current_user)):
        perms = await get_permissions(user)

        if "*" in perms or permission in perms:
            return user

        raise HTTPException(status_code=403, detail="Permission denied")

    return checker