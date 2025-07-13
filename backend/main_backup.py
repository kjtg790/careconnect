from fastapi import FastAPI, Request, Query
import httpx
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
# Import and include router
from care_request_filter import router as care_request_filter_router
from care_request_filter import care_request_filter_router
from apply_care_request import apply_router
from get_active_applications import active_apps_router
from create_caregiver_profile import create_caregiver_profile_router
from check_application_limit import check_application_limit_router
from review_care_applications import review_router
from interview_requests import interview_router
from update_interview_status import update_interview_status_router
from get_interview_requests import interview_get_router
from count_care_applications_by_status import care_app_status_router
from update_interview_request import update_interview_router





# Load environment variables
load_dotenv()

app = FastAPI()
app.include_router(care_app_status_router)
app.include_router(interview_get_router)
app.include_router(update_interview_status_router)
app.include_router(update_interview_router)
app.include_router(care_request_filter_router)
app.include_router(apply_router)
app.include_router(active_apps_router)
app.include_router(create_caregiver_profile_router)
app.include_router(check_application_limit_router)
app.include_router(review_router)
app.include_router(interview_router)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_SERVICE_ROLE_KEY:", SUPABASE_SERVICE_ROLE_KEY[:10], "...")

# POST endpoint to create a care request
@app.post("/api/care-requests")
async def create_care_request(request: Request):
    body = await request.json()
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/care_requests",
            headers=headers,
            json=body
        )
    if response.status_code == 201:
        return response.json()
    else:
        return {
            "error": response.status_code,
            "message": response.text
        }

# GET endpoint to query care request by id or care_request_id
@app.get("/api/care-requests/query")
async def get_care_request(
    id: str = Query(default=None),
    care_request_id: str = Query(default=None)
):
    if not id and not care_request_id:
        return {"error": "Please provide either 'id' or 'care_request_id'."}

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    query_param = f"id=eq.{id}" if id else f"care_request_id=eq.{care_request_id}"
    url = f"{SUPABASE_URL}/rest/v1/care_requests?{query_param}&select=*"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data[0] if data else {"message": "No matching record found."}
    else:
        return {
            "error": response.status_code,
            "message": response.text
        }

# ✅ NEW GET endpoint to fetch all 'requested' care requests
@app.get("/api/care-requests/requested")
async def list_requested_care_requests():
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    select_fields = ",".join([
        "location",
        "care_request_id",
        "id",
        "recipient_age_range",
        "care_services_needed",
        "primary_location_type",
        "care_duration",
        "caregiver_requirements",
        "transportation_provided",
        "accommodation_provided",
        "food_provided",
        "daily_working_hours",
        "excluded_schedule_days",
        "estimated_budget",
        "special_needs",
        "additional_expectations",
        "status"
    ])

    url = f"{SUPABASE_URL}/rest/v1/care_requests?status=eq.requested&select={select_fields}&order=created_at.desc"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": response.status_code,
            "message": response.text
        }
