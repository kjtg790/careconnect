from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

update_interview_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Debug: Print env status
print("ENV - SUPABASE_DB_URL:", SUPABASE_URL)
print("ENV - SUPABASE_SERVICE_ROLE_KEY:", "✅" if SUPABASE_SERVICE_ROLE_KEY else "❌ MISSING")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing required environment variables")

# Pydantic model
class InterviewUpdateRequest(BaseModel):
    id: str
    message: Optional[str] = None
    status: Optional[str] = None
    outcome_status: Optional[str] = None
    feedback: Optional[str] = None
    scheduled_date_time: Optional[datetime] = None

@update_interview_router.put("/api/update-interview-simple")
async def update_interview(payload: InterviewUpdateRequest):
    try:
        data = payload.dict(exclude_none=True)
        print("📥 Incoming Payload:", data)

        interview_id = data.pop("id", None)
        if not interview_id:
            raise HTTPException(status_code=400, detail="Interview ID is required")

        if not data:
            raise HTTPException(status_code=400, detail="No fields to update")

        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        url = f"{SUPABASE_URL}/rest/v1/interview_requests?id=eq.{interview_id}"
        print("✏️ PATCH URL:", url)
        print("✏️ PATCH Body:", data)

        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=headers, json=data)
            print("✅ PATCH Status:", response.status_code)
            print("✅ PATCH Response:", response.text)

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except Exception as e:
        print("🔥 Unhandled Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
