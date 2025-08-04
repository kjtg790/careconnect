# routers/background_verification_process.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
import requests
from config import settings
from auth.auth_utils import get_authenticated_user_id

router = APIRouter()
security = HTTPBearer()

SUPABASE_URL = settings.SUPABASE_DB_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY

# ======= Pydantic Models =======

class VerificationStatus(str):
    """Valid enum values for verification_status"""
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class BackgroundVerificationInsert(BaseModel):
    caregiver_user_id: Optional[str] = None
    status: Optional[VerificationStatus] = VerificationStatus.NOT_SUBMITTED

class BackgroundVerificationUpdate(BaseModel):
    status: VerificationStatus

class BackgroundVerificationResponse(BaseModel):
    id: str
    caregiver_user_id: str
    status: VerificationStatus

# ======= Insert =======

@router.post("/background-verification/insert", tags=["Background Verification"])
def insert_verification(payload: BackgroundVerificationInsert, caregiver_user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/background_verification_process"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = payload.dict()
    data["caregiver_user_id"] = caregiver_user_id

    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Verification record inserted", "data": response.json()}

# ======= Update =======

@router.put("/background-verification/update", tags=["Background Verification"])
def update_verification(payload: BackgroundVerificationUpdate, caregiver_user_id: str = Depends(get_authenticated_user_id)):
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    url = f"{SUPABASE_URL}/rest/v1/background_verification_process?user_id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    response = requests.patch(url, json=update_data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Verification record updated", "data": response.json()}

# ======= Query =======

@router.get("/background-verification/query", tags=["Background Verification"], response_model=list[BackgroundVerificationResponse])
def get_verification(caregiver_user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/background_verification_process?caregiver_user_id=eq.{caregiver_user_id}&select=*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
