from fastapi import APIRouter, Depends, HTTPException
from utils.security import get_current_user
from services import review_service
import logging

router = APIRouter(prefix="/admin/review", tags=["Admin Review"])

logger = logging.getLogger("admin-review")


@router.get("/all")
async def get_all_reviews(user=Depends(get_current_user)):
    """List all reviews for admin moderation."""
    user_roles = user.get("roles", [])
    if not any(role in {"admin", "super_admin"} for role in user_roles):
        raise HTTPException(status_code=403, detail="Permission denied")

    reviews = await review_service.get_all_reviews()

    res_reviews = []
    for r in reviews:
        review_at = r.get("review_at")
        if review_at:
            from datetime import datetime
            if isinstance(review_at, datetime):
                date_str = review_at.strftime("%Y-%m-%d %H:%M")
            else:
                date_str = str(review_at)[:16]
        else:
            date_str = "N/A"

        res_reviews.append({
            "id": r.get("_id"),
            "product_id": r.get("product_id", ""),
            "product_name": r.get("product_name", "Unknown Product"),
            "user_id": r.get("user_id", ""),
            "user_name": r.get("user_name", "Anonymous"),
            "rating": r.get("rating", 0),
            "comment": r.get("comment", ""),
            "verified_purchase": r.get("verified_purchase", False),
            "date": date_str,
        })

    logger.info(f"Returning {len(res_reviews)} reviews to admin")
    return {"success": True, "data": res_reviews}


@router.delete("/delete/{review_id}")
async def delete_review(review_id: str, user=Depends(get_current_user)):
    """Admin delete any review."""
    user_roles = user.get("roles", [])
    if not any(role in {"admin", "super_admin"} for role in user_roles):
        raise HTTPException(status_code=403, detail="Permission denied")

    await review_service.admin_delete_review(review_id)
    return {"success": True, "message": "Review deleted successfully"}
