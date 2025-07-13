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

# ======= MODELS =======

class CareServiceInsert(BaseModel):
    care_request_id: str
    status: str
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    working_hours: Optional[str] = None
    monthly_charges: Optional[float] = None
    weekly_holiday: Optional[str] = None
    food_provided: Optional[bool] = False
    transport_provided: Optional[bool] = False
    assignment_notes: Optional[str] = None

class CareServiceUpdate(BaseModel):
    id: str
    status: Optional[str] = None
    end_date: Optional[str] = None
    working_hours: Optional[str] = None
    monthly_charges: Optional[float] = None
    weekly_holiday: Optional[str] = None
    food_provided: Optional[bool] = None
    transport_provided: Optional[bool] = None
    assignment_notes: Optional[str] = None
    caregiver_cancellation_response: Optional[str] = None
    cancellation_reason: Optional[str] = None

class CareService(BaseModel):
    id: str
    care_request_id: str
    caregiver_user_id: str
    status: str
    start_date: Optional[str]
    end_date: Optional[str]
    working_hours: Optional[str]
    monthly_charges: Optional[float]
    weekly_holiday: Optional[str]
    food_provided: Optional[bool]
    transport_provided: Optional[bool]
    assignment_notes: Optional[str]

# ======= INSERT =======

@router.post("/care_services/insert", tags=["Care Services"])
def insert_care_service(
    payload: CareServiceInsert,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/care_services"
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

    return {"message": "Care service created", "data": response.json()}

# ======= UPDATE =======

@router.put("/care_services/update", tags=["Care Services"])
def update_care_service(
    payload: CareServiceUpdate,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/care_services?id=eq.{payload.id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = {k: v for k, v in payload.dict().items() if v is not None}
    if "cancellation_reason" in data:
        data["cancellation_requested_by"] = user_id

    response = requests.patch(url, json=data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Care service updated", "data": response.json()}

# ======= QUERY (All Services for Caregiver) =======

@router.get("/care_services/query", tags=["Care Services"], response_model=List[CareService])
def get_my_care_services(user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/care_services?caregiver_user_id=eq.{user_id}&select=*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
