from fastapi import APIRouter, Depends, HTTPException
from db import db
from utils.security import get_current_user
from datetime import datetime
from typing import List
import logging

router = APIRouter(prefix="/admin/customer", tags=["Admin Customer"])
logger = logging.getLogger("admin-customer")

PAID_STATUSES = ["CONFIRMED", "SHIPPED", "DISPATCHED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]

@router.get("/all")
async def get_all_customers(user=Depends(get_current_user)):
    # Verify admin permissions
    user_roles = user.get("roles", [])
    if not any(role in {"admin", "super_admin"} for role in user_roles):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Fetch all orders that have successful payment status
    orders = await db.orders.find({"status": {"$in": PAID_STATUSES}}).to_list(length=10000)

    # Group orders by user_id to compute stats
    user_orders = {}
    for order in orders:
        uid = order.get("user_id")
        if isinstance(uid, dict):  # Legacy nested user documents fallback
            uid = uid.get("_id")
        if not uid:
            continue
        if uid not in user_orders:
            user_orders[uid] = []
        user_orders[uid].append(order)

    # Fetch corresponding user documents for these user IDs
    user_ids = list(user_orders.keys())
    users = []
    if user_ids:
        users = await db.users.find({"_id": {"$in": user_ids}}).to_list(length=len(user_ids))
    user_map = {u["_id"]: u for u in users}

    customers_list = []
    for uid, o_list in user_orders.items():
        u_info = user_map.get(uid, {})
        
        # Sort user orders by creation date to find first/last
        o_list_sorted = sorted(
            o_list, 
            key=lambda x: x.get("order_created_at") or x.get("created_at") or datetime.min
        )
        
        first_order_date = o_list_sorted[0].get("order_created_at") or o_list_sorted[0].get("created_at")
        last_order_date = o_list_sorted[-1].get("order_created_at") or o_list_sorted[-1].get("created_at")
        
        # Join date format
        join_date = u_info.get("user_created_at") or first_order_date or datetime.utcnow()
        if isinstance(join_date, datetime):
            join_date_str = join_date.strftime("%Y-%m-%d")
        else:
            join_date_str = str(join_date)[:10]

        first_order_str = first_order_date.strftime("%Y-%m-%d") if isinstance(first_order_date, datetime) else str(first_order_date)[:10]
        last_order_str = last_order_date.strftime("%Y-%m-%d") if isinstance(last_order_date, datetime) else str(last_order_date)[:10]

        total_orders = len(o_list)
        total_spent_val = sum(o.get("total_amount", 0.0) for o in o_list)
        
        # Extract phone
        phone = u_info.get("phone_no") or u_info.get("phone") or ""
        
        # Try to find shipping country from orders, default to "in"
        country = "in"
        for o in reversed(o_list_sorted):  # check newest first
            addr = o.get("address")
            if addr and isinstance(addr, dict):
                country_str = addr.get("country")
                if country_str:
                    c_norm = country_str.lower().strip()
                    if "india" in c_norm or c_norm == "in":
                        country = "in"
                    elif "united states" in c_norm or c_norm == "us":
                        country = "us"
                    elif "canada" in c_norm or c_norm == "ca":
                        country = "ca"
                    elif len(c_norm) > 2:
                        country = c_norm[:2]
                    else:
                        country = c_norm
                    break

        name = u_info.get("users_name") or u_info.get("name") or u_info.get("email", "Guest").split("@")[0]

        customers_list.append({
            "id": uid,
            "name": name,
            "email": u_info.get("email", ""),
            "phone": phone,
            "totalOrders": total_orders,
            "totalSpent": f"₹{total_spent_val:,.2f}",
            "joinDate": join_date_str,
            "firstOrderDate": first_order_str,
            "lastOrderDate": last_order_str,
            "country": country,
            "status": "Active"
        })

    logger.info(f"Returning {len(customers_list)} live customers to admin")
    return {"success": True, "data": customers_list}


@router.get("/{customer_id}")
async def get_customer_detail(customer_id: str, user=Depends(get_current_user)):
    user_roles = user.get("roles", [])
    if not any(role in {"admin", "super_admin"} for role in user_roles):
        raise HTTPException(status_code=403, detail="Permission denied")

    u_info = await db.users.find_one({"_id": customer_id})
    if not u_info:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Fetch orders
    orders = await db.orders.find({
        "user_id": customer_id,
        "status": {"$in": PAID_STATUSES}
    }).to_list(length=100)

    # Sort orders by date descending
    orders_sorted = sorted(
        orders,
        key=lambda x: x.get("order_created_at") or x.get("created_at") or datetime.min,
        reverse=True
    )

    recent_orders = []
    activity = []
    total_spent_val = 0.0

    for o in orders_sorted:
        o_date = o.get("order_created_at") or o.get("created_at") or datetime.utcnow()
        o_date_str = o_date.strftime("%Y-%m-%d") if isinstance(o_date, datetime) else str(o_date)[:10]
        
        items = o.get("items") or []
        products_count = sum(item.get("quantity") or item.get("order_quantity") or 1 for item in items)
        total_amount = o.get("total_amount", 0.0)
        total_spent_val += total_amount

        recent_orders.append({
            "id": o.get("_id"),
            "date": o_date_str,
            "items": products_count,
            "total": f"₹{total_amount:,.2f}",
            "status": o.get("status", "CONFIRMED")
        })

        activity.append({
            "date": o_date_str,
            "action": f"Placed order {o.get('_id')}"
        })

    # Add join date activity
    join_date = u_info.get("user_created_at") or (orders_sorted[-1].get("created_at") if orders_sorted else datetime.utcnow())
    join_date_str = join_date.strftime("%Y-%m-%d") if isinstance(join_date, datetime) else str(join_date)[:10]
    
    activity.append({
        "date": join_date_str,
        "action": "Account created & joined"
    })

    # Sort activity by date descending
    activity.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Get country from latest order or default
    country = "in"
    if orders_sorted:
        addr = orders_sorted[0].get("address")
        if addr and isinstance(addr, dict):
            c_str = addr.get("country")
            if c_str:
                c_norm = c_str.lower().strip()
                if "india" in c_norm or c_norm == "in":
                    country = "in"
                elif "united states" in c_norm or c_norm == "us":
                    country = "us"
                elif "canada" in c_norm or c_norm == "ca":
                    country = "ca"
                elif len(c_norm) > 2:
                    country = c_norm[:2]
                else:
                    country = c_norm

    phone = u_info.get("phone_no") or u_info.get("phone") or ""
    name = u_info.get("users_name") or u_info.get("name") or u_info.get("email", "Guest").split("@")[0]

    return {
        "success": True,
        "data": {
            "id": customer_id,
            "name": name,
            "email": u_info.get("email", ""),
            "phone": phone,
            "joinDate": join_date_str,
            "country": country,
            "status": "Active",
            "totalOrders": len(orders_sorted),
            "totalSpent": f"₹{total_spent_val:,.2f}",
            "recentOrders": recent_orders,
            "activity": activity
        }
    }
