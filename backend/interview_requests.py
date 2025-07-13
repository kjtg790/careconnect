from fastapi import APIRouter, Request, Depends, HTTPException
import httpx
import os
from dotenv import load_dotenv
import json

load_dotenv()

interview_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

@interview_router.post("/api/schedule-interview")
async def schedule_interview(request: Request):
    try:
        data = await request.json()
        print(f"📝 Received data: {json.dumps(data, indent=2)}")

        care_request_id = data.get("care_request_id")
        requester_id = data.get("requester_id")  # current logged-in user
        scheduled_date_time = data.get("scheduled_date_time")
        message = data.get("message")

        if not care_request_id or not requester_id or not scheduled_date_time:
            raise HTTPException(status_code=400, detail="Missing care_request_id, requester_id or scheduled_date_time")

        # Step 1: Query care_applications to get caregiver_user_id + care_application_id
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
        }

        query_url = f"{SUPABASE_URL}/rest/v1/care_applications?care_request_id=eq.{care_request_id}&careseeker_user_id=eq.{requester_id}&select=id,caregiver_user_id"

        async with httpx.AsyncClient() as client:
            resp = await client.get(query_url, headers=headers)

        if resp.status_code != 200 or not resp.json():
            raise HTTPException(status_code=404, detail="Matching care_application not found")

        result = resp.json()[0]
        care_application_id = result["id"]
        caregiver_user_id = result["caregiver_user_id"]

        # Step 2: Insert into interview_requests
        payload = {
            "requester_id": requester_id,
            "caregiver_user_id": caregiver_user_id,
            "care_application_id": care_application_id,
            "scheduled_date_time": scheduled_date_time,
            "message": message,
            "status": "scheduled"
        }

        insert_headers = {
            **headers,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        async with httpx.AsyncClient() as client:
            insert_resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/interview_requests",
                headers=insert_headers,
                json=payload
            )

        if insert_resp.status_code == 201:
            return insert_resp.json()
        else:
            raise HTTPException(status_code=insert_resp.status_code, detail=insert_resp.text)

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
