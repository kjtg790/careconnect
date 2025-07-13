from fastapi import APIRouter, Request
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

apply_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

@apply_router.post("/api/apply-care-request")
async def apply_for_care_request(request: Request):
    data = await request.json()
    care_request_id = data.get("care_request_id")
    user_id = data.get("user_id")  # From logged-in user (ReactJS)

    if not care_request_id or not user_id:
        return {"error": "Both care_request_id and user_id are required."}

    # Step 1: Get careseeker_user_id from care_requests
    async with httpx.AsyncClient() as client:
        get_resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/care_requests?id=eq.{care_request_id}&select=user_id",
            headers=headers
        )

    if get_resp.status_code != 200 or not get_resp.json():
        return {"error": "Invalid care_request_id or not found", "details": get_resp.text}

    care_request = get_resp.json()[0]
    careseeker_user_id = care_request["user_id"]

    # Step 2: Insert into care_applications
    payload = {
        "care_request_id": care_request_id,
        "careseeker_user_id": careseeker_user_id,
        "caregiver_user_id": user_id,
        "status": "pending-under review"
    }

    async with httpx.AsyncClient() as client:
        insert_resp = await client.post(
            f"{SUPABASE_URL}/rest/v1/care_applications",
            headers={**headers, "Prefer": "return=representation"},
            json=payload
        )

    if insert_resp.status_code == 201:
        return insert_resp.json()
    else:
        return {
            "error": insert_resp.status_code,
            "message": insert_resp.text
        }
