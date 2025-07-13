# check_application_limit.py

from fastapi import APIRouter, Query
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

check_application_limit_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

@check_application_limit_router.get("/api/check-application-limit")
async def check_application_limit(caregiver_user_id: str = Query(...)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/care_applications?caregiver_user_id=eq.{caregiver_user_id}&select=id",
            headers=headers
        )

    if response.status_code != 200:
        return {
            "error": "Failed to fetch application records",
            "status_code": response.status_code,
            "details": response.text
        }

    applications = response.json()
    count = len(applications)
    limit_reached = count >= 3

    return {
        "application_count": count,
        "limit_reached": limit_reached
    }
