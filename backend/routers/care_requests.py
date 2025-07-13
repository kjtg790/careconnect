from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import jwt
import requests
from config import settings
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()


class CareRequestBase(BaseModel):
    location: str
    recipient_age_range: str
    care_services_needed: List[str]
    primary_location_type: str
    care_duration: str
    care_start_date_preference: str
    specific_start_date: Optional[str]
    caregiver_requirements: Optional[str]
    transportation_provided: bool
    accommodation_provided: bool
    food_provided: bool
    daily_working_hours: str
    excluded_schedule_days: Optional[str]
    estimated_budget: str
    special_needs: Optional[str]
    additional_expectations: Optional[str]

class CareRequestCreate(CareRequestBase):
    pass

class CareRequestUpdate(CareRequestBase):
    status: Optional[str]

@router.post("/care_requests")
def create_care_request(payload: CareRequestCreate, user_id: str = Depends(get_authenticated_user_id)):
    data = payload.dict()
    data["user_id"] = user_id

    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    response = requests.post(
        f"{settings.SUPABASE_URL}/rest/v1/care_requests",
        json=data,
        headers=headers
    )

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()

@router.put("/care_requests/{request_id}")
def update_care_request(request_id: str, payload: CareRequestUpdate, user_id: str = Depends(get_authenticated_user_id)):
    data = payload.dict(exclude_unset=True)

    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    response = requests.patch(
        f"{settings.SUPABASE_URL}/rest/v1/care_requests?id=eq.{request_id}&user_id=eq.{user_id}",
        json=data,
        headers=headers
    )

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        return response.json()
    except Exception:
        return {"message": "Update successful, but no JSON returned."}

@router.get("/care_requests")
def list_care_requests(
    location: Optional[str] = Query(None),
    recipient_age_range: Optional[str] = Query(None),
    care_services_needed: Optional[str] = Query(None),  # match any one
    primary_location_type: Optional[str] = Query(None),
    care_duration: Optional[str] = Query(None),
    care_start_date_preference: Optional[str] = Query(None),
    specific_start_date: Optional[str] = Query(None),
    caregiver_requirements: Optional[str] = Query(None),
    transportation_provided: Optional[bool] = Query(None),
    accommodation_provided: Optional[bool] = Query(None),
    food_provided: Optional[bool] = Query(None),
    daily_working_hours: Optional[str] = Query(None),
    excluded_schedule_days: Optional[str] = Query(None),
    estimated_budget: Optional[str] = Query(None),
    special_needs: Optional[str] = Query(None),
    additional_expectations: Optional[str] = Query(None),
):
    filter_clauses = []

    if location:
        filter_clauses.append(f"location=ilike.*{location}*")
    if recipient_age_range:
        filter_clauses.append(f"recipient_age_range=eq.{recipient_age_range}")
    if care_services_needed:
        filter_clauses.append(f"care_services_needed=cs.{{{care_services_needed}}}")
    if primary_location_type:
        filter_clauses.append(f"primary_location_type=eq.{primary_location_type}")
    if care_duration:
        filter_clauses.append(f"care_duration=eq.{care_duration}")
    if care_start_date_preference:
        filter_clauses.append(f"care_start_date_preference=eq.{care_start_date_preference}")
    if specific_start_date:
        filter_clauses.append(f"specific_start_date=eq.{specific_start_date}")
    if caregiver_requirements:
        filter_clauses.append(f"caregiver_requirements=ilike.*{caregiver_requirements}*")
    if transportation_provided is not None:
        filter_clauses.append(f"transportation_provided=eq.{str(transportation_provided).lower()}")
    if accommodation_provided is not None:
        filter_clauses.append(f"accommodation_provided=eq.{str(accommodation_provided).lower()}")
    if food_provided is not None:
        filter_clauses.append(f"food_provided=eq.{str(food_provided).lower()}")
    if daily_working_hours:
        filter_clauses.append(f"daily_working_hours=eq.{daily_working_hours}")
    if excluded_schedule_days:
        filter_clauses.append(f"excluded_schedule_days=ilike.*{excluded_schedule_days}*")
    if estimated_budget:
        filter_clauses.append(f"estimated_budget=eq.{estimated_budget}")
    if special_needs:
        filter_clauses.append(f"special_needs=ilike.*{special_needs}*")
    if additional_expectations:
        filter_clauses.append(f"additional_expectations=ilike.*{additional_expectations}*")

    # If no filters, fetch all
    if filter_clauses:
        query_string = "&or=(" + ",".join(filter_clauses) + ")"
    else:
        query_string = ""

    url = f"{settings.SUPABASE_DB_URL}/rest/v1/care_requests?{query_string}&order=created_at.desc"

    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
    }

    response = requests.get(url, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()