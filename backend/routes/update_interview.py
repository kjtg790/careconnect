# routes/update_interview.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import httpx
import os
from auth.auth import get_user_id_from_jwt

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class InterviewUpdate(BaseModel):
    id: str
    message: Optional[str] = None
    status: Optional[str] = None
    outcome_status: Optional[str] = None
    feedback: Optional[str] = None
    scheduled_date_time: Optional[datetime] = None

@router.put("/api/update-interview")
async def update_interview(
    payload: InterviewUpdate,
    user_id: str = Depends(get_user_id_from_jwt)
):
    try:
        print("✅ User ID:", user_id)
        print("📥 Incoming Payload:", payload.dict())

        # Step 1: Check Supabase record
        interview_id = payload.id
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
        }

        check_url = f"{SUPABASE_URL}/rest/v1/interview_requests?id=eq.{interview_id}&select=requester_id,caregiver_user_id"
        async with httpx.AsyncClient() as client:
            print(f"🔍 GET: {check_url}")
            check_resp = await client.get(check_url, headers=headers)
            print("🔍 GET Status:", check_resp.status_code)
            print("🔍 GET Response:", check_resp.text)

        if check_resp.status_code != 200:
            raise HTTPException(status_code=check_resp.status_code, detail="Interview fetch failed")

        records = check_resp.json()
        if not records:
            raise HTTPException(status_code=404, detail="Interview request not found")

        record = records[0]
        if user_id not in [record["requester_id"], record["caregiver_user_id"]]:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # Step 2: Patch the record
        update_data = payload.dict(exclude_none=True)
        update_data.pop("id", None)  # remove id field from patch body

        patch_url = f"{SUPABASE_URL}/rest/v1/interview_requests?id=eq.{interview_id}"
        patch_headers = {
            **headers,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        print(f"📝 PATCH: {patch_url}")
        print("📝 PATCH Body:", update_data)

        async with httpx.AsyncClient() as client:
            patch_resp = await client.patch(patch_url, headers=patch_headers, json=update_data)
            print("📝 PATCH Status:", patch_resp.status_code)
            print("📝 PATCH Response:", patch_resp.text)

        if patch_resp.status_code == 200:
            return patch_resp.json()
        else:
            raise HTTPException(status_code=patch_resp.status_code, detail=f"Update failed: {patch_resp.text}")

    except HTTPException as http_err:
        print("❌ HTTP Error:", http_err.detail)
        raise http_err
    except Exception as e:
        print("🔥 Unexpected Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
