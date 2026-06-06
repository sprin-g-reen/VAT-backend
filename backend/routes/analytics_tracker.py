from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from db import db

router = APIRouter(prefix="/analytics", tags=["Analytics Tracker"])


class TrackEvent(BaseModel):
    page: str
    event_type: str = "view"  # "view" or "click"
    session_id: Optional[str] = None


@router.post("/track")
async def track_page_event(event: TrackEvent, request: Request):
    """
    Records a page view or click event.
    Called by the frontend on every page load.
    """
    # Parse browser from User-Agent
    user_agent = request.headers.get("user-agent", "")
    ua = user_agent.lower()
    if "edg/" in ua or "edge" in ua:
        browser = "edge"
    elif "firefox" in ua:
        browser = "firefox"
    elif "chrome" in ua:
        browser = "chrome"
    elif "safari" in ua:
        browser = "safari"
    else:
        browser = "other"

    # Normalize page name: strip .html extension
    page_name = event.page
    if page_name.endswith(".html"):
        page_name = page_name[:-5]

    # Resolve category name if present in query parameters of Referer URL
    referer = request.headers.get("referer", "")
    if referer:
        try:
            parsed_url = urlparse(referer)
            query_params = parse_qs(parsed_url.query)
            if "category" in query_params:
                cat_id = query_params["category"][0]
                category_map = {
                    "CAT000001": "Beverages",
                    "CAT000002": "Dairy",
                    "CAT000003": "Fruits",
                    "CAT000004": "Snacks",
                    "CAT000005": "Meat"
                }
                if cat_id in category_map:
                    page_name = category_map[cat_id]
                else:
                    # Dynamically look up the category from the database
                    cat_doc = await db.categories.find_one({"_id": cat_id})
                    if cat_doc and "category_name" in cat_doc:
                        page_name = cat_doc["category_name"]
        except Exception:
            pass

    doc = {
        "page": page_name,
        "event_type": event.event_type,
        "session_id": event.session_id,
        "browser": browser,
        "timestamp": datetime.utcnow(),
    }
    await db.page_analytics.insert_one(doc)
    return {"success": True}


