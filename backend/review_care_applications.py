from fastapi import APIRouter, Query
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

review_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
}

@review_router.get("/api/review-care-applications")
async def review_applications(
    care_request_id: str = Query(default=None),
    careseeker_user_id: str = Query(default=None)
):
    if not care_request_id and not careseeker_user_id:
        return {"error": "Provide either care_request_id or careseeker_user_id"}

    # Build query for care_applications
    query_param = ""
    if care_request_id:
        query_param = f"care_request_id=eq.{care_request_id}"
    elif careseeker_user_id:
        query_param = f"careseeker_user_id=eq.{careseeker_user_id}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/care_applications?{query_param}&select=caregiver_user_id,status",
            headers=HEADERS
        )

    if resp.status_code != 200:
        return {"error": "Failed to query care_applications", "details": resp.text}

    care_applications = resp.json()

    # Step 2: For each application, fetch caregiver profile
    profiles_with_status = []
    async with httpx.AsyncClient() as client:
        for app_record in care_applications:
            caregiver_id = app_record["caregiver_user_id"]
            status = app_record["status"]

            profile_resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/caregiver_profiles?user_id=eq.{caregiver_id}&select=*",
                headers=HEADERS
            )

            if profile_resp.status_code == 200 and profile_resp.json():
                profile = profile_resp.json()[0]
                profile["application_status"] = status
                profiles_with_status.append(profile)

    return {"caregiver_applications": profiles_with_status}
