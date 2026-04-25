from fastapi import Depends, HTTPException
from utils.security import get_current_user
from db import db


async def get_permissions(user):
    permissions = set()

    for role in user.get("roles", []):
        role_data = await db.roles.find_one({"name": role})

        if role_data:
            perms = role_data.get("permissions", [])

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