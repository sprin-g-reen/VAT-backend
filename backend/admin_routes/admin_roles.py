from fastapi import APIRouter, Depends
from db import db
from dependencies.roles import require_permission
from pydantic import BaseModel
from typing import List

class RoleCreate(BaseModel):
    name: str
    permissions: List[str]

class AssignRoleRequest(BaseModel):
    roles: List[str]

router = APIRouter(prefix="/admin", tags=["Admin Roles"])


@router.post("/roles")
async def create_role(payload: RoleCreate):
    await db.roles.insert_one({
        "name": payload.name,
        "permissions": payload.permissions
    })

    return {"message": "Role created"}


@router.patch("/admin/users/{user_id}/roles")
async def assign_role(
    user_id: str,
    payload: AssignRoleRequest
):
    await db.users.update_one(
        {"_id": user_id},   #  STRING ID
        {"$set": {"roles": payload.roles}}
    )

    return {"message": "Roles updated"}