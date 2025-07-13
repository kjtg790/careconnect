# get_active_applications.py

from fastapi import APIRouter, Request, Query
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

active_apps_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

@active_apps_router.get("/api/active-care-applications")
async def get_active_care_applications(caregiver_user_id: str = Query(...)):
    # Define status values to exclude
    excluded_statuses = ["pending", "closed", "rejected"]

    # Create Supabase query filter
    status_filter = "status=not.in.(" + ",".join(f'"{s}"' for s in excluded_statuses) + ")"
    user_filter = f"caregiver_user_id=eq.{caregiver_user_id}"

    query = f"{SUPABASE_URL}/rest/v1/care_applications?{user_filter}&{status_filter}&select=care_request_id"

    async with httpx.AsyncClient() as client:
        response = await client.get(query, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": response.status_code,
            "message": response.text
        }
