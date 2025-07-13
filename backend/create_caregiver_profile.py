# create_caregiver_profile.py

from fastapi import APIRouter, Request, Query, HTTPException
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

create_caregiver_profile_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# POST: Create caregiver profile
@create_caregiver_profile_router.post("/api/caregiver-profiles")
async def create_caregiver_profile(request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        return {"error": "Missing user_id (logged-in user)"}
    if "care_services" not in body or not body["care_services"]:
        return {"error": "care_services is required"}

    payload = {
        "user_id": user_id,
        "care_services": body.get("care_services"),
        "experience_description": body.get("experience_description"),
        "certifications": body.get("certifications"),
        "education": body.get("education"),
        "schedule_preferences": body.get("schedule_preferences"),
        "availability_locations": body.get("availability_locations"),
        "limitations_expectations": body.get("limitations_expectations"),
        "expected_charges": body.get("expected_charges"),
        "start_immediately": body.get("start_immediately", False),
        "age_range": body.get("age_range"),
        "full_name": body.get("full_name"),
        "avatar_url": body.get("avatar_url"),
        "interview_availability": body.get("interview_availability"),
        "agency_id": body.get("agency_id"),
        "verification_status": body.get("verification_status", "not_submitted"),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/caregiver_profiles",
            headers={**headers, "Prefer": "return=representation"},
            json=payload
        )

    if response.status_code == 201:
        return response.json()
    else:
        return {
            "error": response.status_code,
            "message": response.text
        }

# GET: Retrieve caregiver profile by user_id
@create_caregiver_profile_router.get("/api/caregiver-profiles")
async def get_caregiver_profile(user_id: str = Query(...)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/caregiver_profiles?user_id=eq.{user_id}&select=*",
            headers=headers
        )

    if response.status_code == 200:
        results = response.json()
        if results:
            return results[0]
        else:
            raise HTTPException(status_code=404, detail="Profile not found")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)

# PATCH: Update caregiver profile
@create_caregiver_profile_router.patch("/api/caregiver-profiles")
async def update_caregiver_profile(request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        return {"error": "user_id is required for update"}

    update_fields = body.copy()
    update_fields.pop("user_id", None)  # don't try to update primary key

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/caregiver_profiles?user_id=eq.{user_id}",
            headers={**headers, "Prefer": "return=representation"},
            json=update_fields
        )

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": response.status_code,
            "message": response.text
        }
