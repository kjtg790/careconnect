from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from config import settings
import jwt
import requests
from typing import Optional, List
from auth.auth_utils import get_authenticated_user_id

router = APIRouter()
security = HTTPBearer()

# Environment variables
SUPABASE_URL = settings.SUPABASE_DB_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
JWT_SECRET = settings.SUPABASE_JWT_SECRET


class InterviewUpdate(BaseModel):
    id: str
    message: Optional[str] = None
    status: Optional[str] = None
    outcome_status: Optional[str] = None
    feedback: Optional[str] = None
    scheduled_date_time: Optional[str] = None  # ISO format expected


class InterviewCreate(BaseModel):
    care_request_id: str
    caregiver_id: str
    scheduled_date_time: Optional[str] = None
    message: Optional[str] = None


@router.put("/update")
def update_interview_request(
    payload: InterviewUpdate,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/interview_requests?id=eq.{payload.id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = {k: v for k, v in payload.dict().items() if v is not None}
    data["requester_id"] = user_id

    response = requests.patch(url, json=data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Supabase error: {response.text}"
        )

    return {"message": "Interview request updated", "data": response.json()}


@router.post("/create")
def insert_interview_request(
    payload: InterviewCreate,
    user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/interview_requests"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = {
        "care_request_id": payload.care_request_id,
        "caregiver_id": payload.caregiver_id,
        "scheduled_date_time": payload.scheduled_date_time,
        "message": payload.message,
        "requester_id": user_id
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Supabase insert error: {response.text}"
        )

    return {"message": "Interview request created", "data": response.json()}


@router.get("/query")
def get_interview_requests(
    user_id: Optional[str] = Query(None, description="User ID for auth context"),
    requester_id: Optional[str] = Query(None, description="Filter by requester_id"),
    caregiver_user_id: Optional[str] = Query(None, description="Filter by caregiver_user_id"),
    status_filter: Optional[str] = Query(None, description="Optional status filter")
):
    filters = []

    # Use fallback user_id to build base OR filter
    if user_id:
        filters.append(f"or=(requester_id.eq.{user_id},caregiver_user_id.eq.{user_id})")

    # Specific requester_id
    if requester_id:
        filters.append(f"requester_id=eq.{requester_id}")

    # Specific caregiver_user_id
    if caregiver_user_id:
        filters.append(f"caregiver_user_id=eq.{caregiver_user_id}")

    # Status
    if status_filter:
        filters.append(f"status=eq.{status_filter}")

    filter_query = "&".join(filters)

    url = f"{SUPABASE_URL}/rest/v1/interview_requests?{filter_query}&order=created_at.desc"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Supabase fetch error: {response.text}"
        )

    return {"message": "Interview requests fetched", "data": response.json()}
