# routers/count_care_applications_by_status.py

from fastapi import APIRouter, Query, Depends, HTTPException
import httpx
import os
from dotenv import load_dotenv
from auth.auth_utils import get_authenticated_user_id

load_dotenv()

care_app_status_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

@care_app_status_router.get("/care-applications/status-count", tags=["Care Applications"])
async def count_care_applications_by_status(
    care_request_id: str = Query(default=None),
    user_id: str = Depends(get_authenticated_user_id)
):
    """
    Count the number of care applications by status.
    Requires authentication and uses the current user's ID for careseeker filtering.
    """
    filters = [f"careseeker_user_id=eq.{user_id}"]

    if care_request_id:
        filters.append(f"care_request_id=eq.{care_request_id}")

    filter_query = "&".join(filters)
    url = f"{SUPABASE_URL}/rest/v1/care_applications?select=status"
    if filter_query:
        url += f"&{filter_query}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    records = response.json()

    # Count statuses
    status_counts = {}
    for record in records:
        status = record.get("status")
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1

    # Convert to list
    return [{"status": k, "count": v} for k, v in status_counts.items()]
