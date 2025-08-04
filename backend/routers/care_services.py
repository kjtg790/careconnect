from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from config import settings
import jwt
import requests
from auth.auth_utils import get_authenticated_user_id
from fastapi import Query
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
def get_my_care_services(
    caregiver_user_id: Optional[str] = Depends(get_authenticated_user_id),
    id: Optional[str] = Query(None),
    care_request_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    working_hours: Optional[str] = Query(None),
    monthly_charges: Optional[float] = Query(None),
    weekly_holiday: Optional[str] = Query(None),
    food_provided: Optional[bool] = Query(None),
    transport_provided: Optional[bool] = Query(None),
    assignment_notes: Optional[str] = Query(None)
):
    """
    Query care services with optional filters
    """
    base_url = f"{SUPABASE_URL}/rest/v1/care_services"
    filters = []

    if caregiver_user_id:
        filters.append(f"caregiver_user_id=eq.{caregiver_user_id}")
    if id:
        filters.append(f"id=eq.{id}")
    if care_request_id:
        filters.append(f"care_request_id=eq.{care_request_id}")
    if status:
        filters.append(f"status=eq.{status}")
    if start_date:
        filters.append(f"start_date=eq.{start_date}")
    if end_date:
        filters.append(f"end_date=eq.{end_date}")
    if working_hours:
        filters.append(f"working_hours=eq.{working_hours}")
    if monthly_charges is not None:
        filters.append(f"monthly_charges=eq.{monthly_charges}")
    if weekly_holiday:
        filters.append(f"weekly_holiday=eq.{weekly_holiday}")
    if food_provided is not None:
        filters.append(f"food_provided=is.{str(food_provided).lower()}")
    if transport_provided is not None:
        filters.append(f"transport_provided=is.{str(transport_provided).lower()}")
    if assignment_notes:
        filters.append(f"assignment_notes=eq.{assignment_notes}")

    query_string = "&".join(filters)
    url = f"{base_url}?select=*" + (f"&{query_string}" if filters else "")

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
