# count_care_applications_by_status.py

from fastapi import APIRouter, Query
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

care_app_status_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

@care_app_status_router.get("/api/care-applications/status-count")
async def count_care_applications_by_status(
    care_request_id: str = Query(default=None),
    requester_user_id: str = Query(default=None)
):
    filters = []

    if care_request_id:
        filters.append(f"care_request_id=eq.{care_request_id}")
    if requester_user_id:
        filters.append(f"careseeker_user_id=eq.{requester_user_id}")

    filter_query = "&".join(filters)
    url = f"{SUPABASE_URL}/rest/v1/care_applications?select=status"

    if filter_query:
        url += f"&{filter_query}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        return {
            "error": response.status_code,
            "message": response.text
        }

    records = response.json()

    # Count occurrences of each status
    status_counts = {}
    for record in records:
        status = record.get("status")
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1

    # Convert to list of objects
    status_list = [{"status": k, "count": v} for k, v in status_counts.items()]

    return status_list
