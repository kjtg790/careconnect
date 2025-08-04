# backend/routers/caregiver_profiles.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import jwt
from config import settings
from auth.auth_utils import get_authenticated_user_id

router = APIRouter(prefix="/api/caregiver-profile", tags=["Caregiver Profile"])
security = HTTPBearer()


# ---- Request model for insert/update ----
class CaregiverProfile(BaseModel):
    care_services: List[str]
    experience_description: Optional[str]
    certifications: Optional[str]
    education: Optional[str]
    schedule_preferences: Optional[Dict[str, Any]]
    availability_locations: Optional[str]
    limitations_expectations: Optional[str]
    expected_charges: Optional[str]
    start_immediately: Optional[bool]
    age_range: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    interview_availability: Optional[Dict[str, Any]]
    agency_id: Optional[str]

# ---- INSERT Profile ----
@router.post("/insert")
def insert_caregiver_profile(
    payload: CaregiverProfile,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{settings.SUPABASE_DB_URL}/rest/v1/caregiver_profiles"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = payload.dict()
    data["user_id"] = user_id

    response = requests.post(url, json=data, headers=headers)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()

# ---- UPDATE Profile ----
@router.put("/update")
def update_caregiver_profile(
    payload: CaregiverProfile,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{settings.SUPABASE_DB_URL}/rest/v1/caregiver_profiles?user_id=eq.{user_id}"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    response = requests.patch(url, json=payload.dict(), headers=headers)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        return {"message": "Profile updated successfully, but no JSON response returned."}

# ---- GET Current User's Profile ----
@router.get("/query")
def get_my_caregiver_profile(
    caregiver_user_id: str = Query(default=None),
    user_id: str = Depends(get_authenticated_user_id)
):
    # Use caregiver_user_id if provided; otherwise, fallback to the authenticated user
    target_user_id = caregiver_user_id or user_id

    url = f"{settings.SUPABASE_DB_URL}/rest/v1/caregiver_profiles?user_id=eq.{target_user_id}"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
