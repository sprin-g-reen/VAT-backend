from fastapi import APIRouter, Depends, HTTPException
from db import db
from utils.security import get_current_user
from datetime import datetime
from typing import List
import logging

router = APIRouter(prefix="/admin/order", tags=["Admin Order"])

logger = logging.getLogger("admin-order")

@router.get("/all")
async def get_all_orders(user=Depends(get_current_user)):
    # Check admin roles
    user_roles = user.get("roles", [])
    if not any(role in {"admin", "super_admin"} for role in user_roles):
        raise HTTPException(status_code=403, detail="Permission denied")
        
    PAID_STATUSES = ["CONFIRMED", "SHIPPED", "DISPATCHED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]
    orders = await db.orders.find({"status": {"$in": PAID_STATUSES}}).to_list(length=1000)
    
    # Fetch user details to embed email and name
    # Normalize user_id values: some orders store a full user document, others store the id string
    user_ids = []
    for o in orders:
        uid = o.get("user_id")
        if isinstance(uid, dict):
            uid = uid.get("_id")
        if uid:
            user_ids.append(uid)
    # Deduplicate while preserving as list
    user_ids = list(set(user_ids))
    users = []
    if user_ids:
        users = await db.users.find({"_id": {"$in": user_ids}}).to_list(length=len(user_ids))
    user_map = {u["_id"]: u for u in users}
    
    res_orders = []
    for o in orders:
        uid = o.get("user_id")
        # Normalize uid for lookup (some orders store full user doc)
        lookup_uid = None
        if isinstance(uid, dict):
            lookup_uid = uid.get("_id")
        else:
            lookup_uid = uid
        u_info = user_map.get(lookup_uid, {})

        # Calculate products count (sum of quantities)
        items = o.get("items") or []
        products_count = sum(item.get("quantity") or item.get("order_quantity") or 1 for item in items)

        # Format total amount to currency
        total_amount = o.get("total_amount", 0.0)

        # Handle date parsing
        order_date = o.get("order_created_at") or o.get("created_at") or datetime.utcnow()
        # Normalize order_date to a datetime for correct sorting
        if isinstance(order_date, datetime):
            sort_date = order_date
            date_str = order_date.strftime("%Y-%m-%d")
        else:
            try:
                # Try parsing common ISO formats
                sort_date = datetime.fromisoformat(str(order_date))
                date_str = sort_date.strftime("%Y-%m-%d")
            except Exception:
                # Fallback: use utcnow and log unexpected format
                logger.warning(f"Unexpected order date format for order {o.get('_id')}: {order_date}")
                sort_date = datetime.utcnow()
                date_str = sort_date.strftime("%Y-%m-%d")

        res_orders.append({
            "id": o.get("_id"),
            "orderNumber": o.get("_id"),
            "customerName": u_info.get("name") or u_info.get("email", "Guest").split("@")[0],
            "customerImage": "https://randomuser.me/api/portraits/men/10.jpg",
            "email": u_info.get("email", ""),
            "total": f"₹{total_amount:,.2f}",
            "products": products_count,
            "date": date_str,
            "status": o.get("status", "PENDING"),
            "_sort_date": sort_date,
        })
        
    # Sort orders by actual datetime descending
    res_orders.sort(key=lambda x: x.get("_sort_date", datetime.utcnow()), reverse=True)
    # Remove internal sort key before returning
    for r in res_orders:
        r.pop("_sort_date", None)
    logger.info(f"Returning {len(res_orders)} orders to admin")
    return {"success": True, "data": res_orders}


@router.get("/all_debug")
async def get_all_orders_debug():
    """Temporary debug endpoint: returns orders without authentication.
    Use only for local debugging; remove in production."""
    PAID_STATUSES = ["CONFIRMED", "SHIPPED", "DISPATCHED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]
    orders = await db.orders.find({"status": {"$in": PAID_STATUSES}}).to_list(length=1000)
    res = []
    for o in orders:
        items = o.get("items") or []
        products_count = sum(item.get("quantity") or item.get("order_quantity") or 1 for item in items)
        total_amount = o.get("total_amount", 0.0)
        order_date = o.get("order_created_at") or o.get("created_at") or datetime.utcnow()
        if isinstance(order_date, datetime):
            date_str = order_date.strftime("%Y-%m-%d")
        else:
            date_str = str(order_date)[:10]
        res.append({
            "id": o.get("_id"),
            "orderNumber": o.get("_id"),
            "customerName": o.get("user_id") or "Guest",
            "email": "",
            "total": f"₹{total_amount:,.2f}",
            "products": products_count,
            "date": date_str,
            "status": o.get("status", "PENDING"),
        })
    return {"success": True, "data": res}

@router.patch("/status/{order_id}")
async def update_order_status(order_id: str, payload: dict, user=Depends(get_current_user)):
    user_roles = user.get("roles", [])
    if not any(role in {"admin", "super_admin"} for role in user_roles):
        raise HTTPException(status_code=403, detail="Permission denied")
        
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")
        
    result = await db.orders.update_one(
        {"_id": order_id},
        {"$set": {"status": status.upper()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
        
    return {"success": True, "message": "Order status updated successfully"}
