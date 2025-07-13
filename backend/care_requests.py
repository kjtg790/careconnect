from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from auth.auth_utils import get_authenticated_user_id

from utils import make_supabase_request

router = APIRouter()

@router.get("/api/care-requests")
async def get_care_requests(user_id: str, user_id_from_token: str = Depends(get_authenticated_user_id)):
    """Get care requests for a user"""
    try:
        response = await make_supabase_request(
            "GET", 
            "care_requests",
            params={"user_id": f"eq.{user_id}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error fetching care requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/api/care-requests/{request_id}/withdraw")
async def withdraw_care_request(
    request_id: str, 
    request: Request,
    user_id_from_token: str = Depends(get_authenticated_user_id)
):
    """Withdraw a care request"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        status = data.get("status", "cancelled_withdrawn")
        
        # Update care request status
        response = await make_supabase_request(
            "PATCH",
            f"care_requests?id=eq.{request_id}",
            {"status": status}
        )
        
        if response.status_code == 200:
            # Log status history
            await make_supabase_request(
                "POST",
                "care_request_status_history",
                {
                    "care_request_id": request_id,
                    "status": status,
                    "changed_by_user_id": user_id,
                    "changed_by_user_role": "care_seeker"
                }
            )
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error withdrawing care request: {e}")
        raise HTTPException(status_code=500, detail=str(e))