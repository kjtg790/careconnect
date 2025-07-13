# backend/routers/care_applications.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from config import settings
import jwt
import requests
from auth.auth_utils import get_authenticated_user_id

router = APIRouter()
security = HTTPBearer()

SUPABASE_URL = settings.SUPABASE_DB_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
JWT_SECRET = settings.SUPABASE_JWT_SECRET

# Schemas
class CareApplicationCreate(BaseModel):
    care_request_id: str

class CareApplicationUpdate(BaseModel):
    id: str
    status: str

class CareApplication(BaseModel):
    id: str
    care_request_id: str
    caregiver_user_id: str
    careseeker_user_id: Optional[str]
    status: str
    created_at: str
    updated_at: str


# Insert
@router.post("/care_applications/insert", tags=["Care Applications"])
def insert_care_application(
    payload: CareApplicationCreate,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/care_applications"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = {
        "care_request_id": payload.care_request_id,
        "caregiver_user_id": user_id
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Care application submitted", "data": response.json()}

# Update
@router.put("/care_applications/update", tags=["Care Applications"])
def update_care_application(
    payload: CareApplicationUpdate,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/care_applications?id=eq.{payload.id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = {
        "status": payload.status,
        "careseeker_user_id": user_id
    }

    response = requests.patch(url, json=data, headers=headers)

    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Care application updated", "data": response.json()}

# Query all applications by logged-in caregiver
@router.get("/care_applications/query", tags=["Care Applications"], response_model=List[CareApplication])
def query_care_applications(user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/care_applications?caregiver_user_id=eq.{user_id}&select=*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
