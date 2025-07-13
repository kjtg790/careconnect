# get_interview_requests.py

from fastapi import APIRouter, Request, Query
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

interview_get_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

@interview_get_router.get("/api/get-interview-requests")
async def get_interview_requests(
    requester_user_id: str = Query(default=None),
    caregiver_user_id: str = Query(default=None)
):
    filters = []

    if requester_user_id:
        filters.append(f"requester_id=eq.{requester_user_id}")
    if caregiver_user_id:
        filters.append(f"caregiver_user_id=eq.{caregiver_user_id}")

    filter_query = "&".join(filters)
    base_url = f"{SUPABASE_URL}/rest/v1/interview_requests"

    # Add select and ordering clause
    query_string = f"{filter_query}&select=*&order=updated_at.desc" if filter_query else "select=*&order=updated_at.desc"
    url = f"{base_url}?{query_string}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": response.status_code,
            "message": response.text
        }
