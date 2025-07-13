# update_interview_status.py

from fastapi import APIRouter, Request, HTTPException
import httpx
import os
from dotenv import load_dotenv
from utils import get_user_id_from_jwt  # assumes you already have this utility

load_dotenv()

update_interview_status_router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

@update_interview_status_router.put("/api/interviews/{interview_id}/status")
async def update_interview_status(interview_id: str, request: Request):
    body = await request.json()

    status = body.get("status")
    feedback = body.get("feedback")
    outcome_status = body.get("outcome_status")

    # Optional: You could validate user owns this interview using JWT user_id
    requester_user_id = get_user_id_from_jwt(request)

    if not status or status not in ["accepted", "declined", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid or missing status")

    update_data = {"status": status}
    if feedback:
        update_data["feedback"] = feedback
    if outcome_status:
        update_data["outcome_status"] = outcome_status

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/interview_requests?id=eq.{interview_id}",
            headers={**headers, "Prefer": "return=representation"},
            json=update_data
        )

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}
