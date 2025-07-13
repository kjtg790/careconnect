# routers/agencies.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import requests
import jwt
from config import settings
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()

SUPABASE_URL = settings.SUPABASE_DB_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
JWT_SECRET = settings.SUPABASE_JWT_SECRET

# ======= Models =======

class AgencyInsert(BaseModel):
    agency_name: str
    contact_person: str
    phone_number: str
    business_address: str
    license_number: Optional[str] = None

class AgencyUpdate(BaseModel):
    agency_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    business_address: Optional[str] = None
    license_number: Optional[str] = None

class AgencyResponse(BaseModel):
    id: str
    user_id: str
    agency_name: str
    contact_person: str
    phone_number: str
    business_address: str
    license_number: Optional[str]

# ======= Insert =======

@router.post("/agencies/insert", tags=["Agencies"])
def insert_agency(payload: AgencyInsert, user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/agencies"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = payload.dict()
    data["user_id"] = user_id

    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Agency profile created", "data": response.json()}

# ======= Update =======

@router.put("/agencies/update", tags=["Agencies"])
def update_agency(payload: AgencyUpdate, user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/agencies?user_id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    update_data = {k: v for k, v in payload.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    response = requests.patch(url, json=update_data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Agency profile updated", "data": response.json()}

# ======= Query =======

@router.get("/agencies/query", tags=["Agencies"], response_model=Optional[AgencyResponse])
def get_agency(user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/agencies?user_id=eq.{user_id}&select=*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()
    if not data:
        return None

    return data[0]
