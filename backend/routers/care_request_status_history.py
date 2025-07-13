# care_request_status_history.py

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

# ========= Pydantic Models =========

class StatusHistoryCreate(BaseModel):
    care_request_id: str
    status: str  # Enum from care_request_status (assumed validated by DB)
    changed_by_user_role: str  # Enum from app_role (assumed validated by DB)

class StatusHistoryUpdate(BaseModel):
    status: Optional[str] = None
    changed_by_user_role: Optional[str] = None

# ========= Insert =========

@router.post("/care-status-history/insert", tags=["Care Request Status History"])
def insert_status_history(payload: StatusHistoryCreate, user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/care_request_status_history"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = payload.dict()
    data["changed_by_user_id"] = user_id

    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Status history inserted", "data": response.json()}

# ========= Update =========

@router.put("/care-status-history/update", tags=["Care Request Status History"])
def update_status_history(record_id: str, payload: StatusHistoryUpdate, user_id: str = Depends(get_authenticated_user_id)):
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    url = f"{SUPABASE_URL}/rest/v1/care_request_status_history?id=eq.{record_id}&changed_by_user_id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    response = requests.patch(url, json=update_data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Status history updated", "data": response.json()}

# ========= Query =========

@router.get("/care-status-history/query", tags=["Care Request Status History"])
def query_status_history(care_request_id: Optional[str] = None, user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/care_request_status_history"
    params = {
        "changed_by_user_id": f"eq.{user_id}",
        "select": "*"
    }
    if care_request_id:
        params["care_request_id"] = f"eq.{care_request_id}"

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
