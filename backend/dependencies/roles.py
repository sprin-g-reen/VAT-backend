from fastapi import Depends, HTTPException
from utils.security import get_current_user
from db import db


from redis_db import redis_client
import json

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