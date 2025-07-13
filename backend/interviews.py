from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from auth.auth import get_user_id_from_jwt
from utils import make_supabase_request

router = APIRouter()

@router.get("/api/get-interview-requests")
async def get_interview_requests(
    requester_user_id: Optional[str] = None,
    caregiver_user_id: Optional[str] = None,
    user_id_from_token: str = Depends(get_user_id_from_jwt)
):
    """Get interview requests"""
    try:
        params = {}
        if requester_user_id:
            params["requester_id"] = f"eq.{requester_user_id}"
        if caregiver_user_id:
            params["caregiver_user_id"] = f"eq.{caregiver_user_id}"
        
        response = await make_supabase_request(
            "GET",
            "interview_requests",
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error fetching interview requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/schedule-interview")
async def schedule_interview(
    request: Request,
    user_id_from_token: str = Depends(get_user_id_from_jwt)
):
    """Schedule an interview"""
    try:
        data = await request.json()
        
        payload = {
            "requester_id": user_id_from_token,
            "caregiver_user_id": data.get("caregiver_user_id"),
            "care_request_id": data.get("care_request_id"),
            "care_application_id": data.get("care_application_id"),
            "scheduled_date_time": data.get("scheduled_date_time"),
            "message": data.get("message"),
            "status": "scheduled"
        }
        
        response = await make_supabase_request(
            "POST",
            "interview_requests",
            payload
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error scheduling interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/update-interview")
async def update_interview(
    request: Request,
    user_id_from_token: str = Depends(get_user_id_from_jwt)
):
    """Update interview status"""
    try:
        data = await request.json()
        interview_id = data.get("interview_id")
        
        # Verify ownership
        check_response = await make_supabase_request(
            "GET",
            f"interview_requests?id=eq.{interview_id}"
        )
        
        if check_response.status_code == 200:
            interviews = check_response.json()
            if not interviews:
                raise HTTPException(status_code=404, detail="Interview not found")
            
            interview = interviews[0]
            if interview["requester_id"] != user_id_from_token and interview["caregiver_user_id"] != user_id_from_token:
                raise HTTPException(status_code=403, detail="Not authorized to update this interview")
        
        response = await make_supabase_request(
            "PATCH",
            f"interview_requests?id=eq.{interview_id}",
            data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error updating interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))