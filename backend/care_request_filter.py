# care_request_filter.py

from fastapi import APIRouter, Query
from typing import Optional, List
from urllib.parse import quote
import httpx
import os
from dotenv import load_dotenv


care_request_filter_router = APIRouter()

load_dotenv()

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

@care_request_filter_router.get("/api/care-requests/filter")
async def filter_care_requests(
    care_request_id: Optional[str] = None,
    id: Optional[str] = None,
    location: Optional[str] = None,
    care_duration: Optional[str] = None,
    estimated_budget: Optional[str] = None,
    daily_working_hours: Optional[str] = None,
    excluded_schedule_days: Optional[str] = None,
    recipient_age_range: Optional[str] = None,
    care_services_needed: Optional[List[str]] = Query(None),
    primary_location_type: Optional[str] = None,
    caregiver_requirements: Optional[str] = None,
    transportation_provided: Optional[bool] = None,
    accommodation_provided: Optional[bool] = None,
    food_provided: Optional[bool] = None,
    special_needs: Optional[str] = None,
    additional_expectations: Optional[str] = None,
):
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }

    filters = []

    # Text or exact match fields
    if location:
        filters.append(f"care_request_id=eq.{quote(care_request_id)}")
    if location:
        filters.append(f"location=eq.{quote(location)}")
    if care_duration:
        filters.append(f"care_duration=eq.{quote(care_duration)}")
    if estimated_budget:
        filters.append(f"estimated_budget=eq.{quote(estimated_budget)}")
    if daily_working_hours:
        filters.append(f"daily_working_hours=eq.{quote(daily_working_hours)}")
    if excluded_schedule_days:
        filters.append(f"excluded_schedule_days=eq.{quote(excluded_schedule_days)}")
    if recipient_age_range:
        filters.append(f"recipient_age_range=eq.{quote(recipient_age_range)}")
    if primary_location_type:
        filters.append(f"primary_location_type=eq.{quote(primary_location_type)}")
    if caregiver_requirements:
        filters.append(f"caregiver_requirements=eq.{quote(caregiver_requirements)}")
    if transportation_provided is not None:
        filters.append(f"transportation_provided=is.{str(transportation_provided).lower()}")
    if accommodation_provided is not None:
        filters.append(f"accommodation_provided=is.{str(accommodation_provided).lower()}")
    if food_provided is not None:
        filters.append(f"food_provided=is.{str(food_provided).lower()}")
    if special_needs:
        filters.append(f"special_needs=eq.{quote(special_needs)}")
    if additional_expectations:
        filters.append(f"additional_expectations=eq.{quote(additional_expectations)}")

    # Array field - care_services_needed
    if care_services_needed:
        for service in care_services_needed:
            filters.append(f"care_services_needed=cs.{{{quote(service)}}}")

    # Combine all filters
    filter_query = "&".join(filters)
    if filter_query:
        url = f"{SUPABASE_URL}/rest/v1/care_requests?{filter_query}&order=created_at.desc"
    else:
        url = f"{SUPABASE_URL}/rest/v1/care_requests?order=created_at.desc"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": response.status_code,
            "message": response.text
        }
