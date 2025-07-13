# routers/care_disputes.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt
import requests
from config import settings
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()

SUPABASE_URL = settings.SUPABASE_DB_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
JWT_SECRET = settings.SUPABASE_JWT_SECRET

# ======= Pydantic Models =======

class DisputeCreate(BaseModel):
    care_service_id: str
    care_request_id: str
    caregiver_user_id: str
    dispute_reason: str
    dispute_details: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = "medium"

class DisputeUpdate(BaseModel):
    status: Optional[str] = None
    resolved_at: Optional[str] = None
    dispute_details: Optional[str] = None
    admin_notes: Optional[str] = None
    assigned_admin_id: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None

# ======= Insert =======

@router.post("/care-disputes/insert", tags=["Care Disputes"])
def insert_dispute(payload: DisputeCreate, user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/care_disputes"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = payload.dict()
    data["care_receiver_user_id"] = user_id

    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Dispute created", "data": response.json()}

# ======= Update =======

@router.put("/care-disputes/update", tags=["Care Disputes"])
def update_dispute(dispute_id: str, payload: DisputeUpdate, user_id: str = Depends(get_authenticated_user_id)):
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    url = f"{SUPABASE_URL}/rest/v1/care_disputes?id=eq.{dispute_id}&care_receiver_user_id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    response = requests.patch(url, json=update_data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Dispute updated", "data": response.json()}

# ======= Query =======

@router.get("/care-disputes/query", tags=["Care Disputes"])
def query_my_disputes(user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/care_disputes?care_receiver_user_id=eq.{user_id}&select=*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
