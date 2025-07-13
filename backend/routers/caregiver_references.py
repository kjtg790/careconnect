from fastapi import APIRouter, Depends, HTTPException
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

# ======= Models =======

class CaregiverReferenceInsert(BaseModel):
    name: str
    phone_number: str
    email: str

class CaregiverReferenceUpdate(BaseModel):
    id: str
    status: Optional[str] = None
    referenced_by_user_id: Optional[str] = None

class CaregiverReference(BaseModel):
    id: str
    caregiver_user_id: str
    name: str
    phone_number: str
    email: str
    status: str

# ======= Insert =======

@router.post("/caregiver_references/insert", tags=["Caregiver References"])
def insert_reference(
    payload: CaregiverReferenceInsert,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/caregiver_references"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = payload.dict()
    data["caregiver_user_id"] = user_id

    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Reference added", "data": response.json()}

# ======= Update =======

@router.put("/caregiver_references/update", tags=["Caregiver References"])
def update_reference(
    payload: CaregiverReferenceUpdate,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/caregiver_references?id=eq.{payload.id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = {k: v for k, v in payload.dict().items() if v is not None}
    if "referenced_by_user_id" not in data:
        data["referenced_by_user_id"] = user_id

    response = requests.patch(url, json=data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Reference updated", "data": response.json()}

# ======= Query (All References for Logged-In Caregiver) =======

@router.get("/caregiver_references/query", tags=["Caregiver References"], response_model=List[CaregiverReference])
def query_references(user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/caregiver_references?caregiver_user_id=eq.{user_id}&select=*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
