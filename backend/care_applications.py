from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from auth.auth_utils import get_authenticated_user_id
from utils import make_supabase_request
from models import ApplyRequest

router = APIRouter()

@router.get("/api/care-applications/status-count")
async def get_application_status_counts(
    care_request_id: str,
    requester_user_id: str,
    user_id_from_token: str = Depends(get_authenticated_user_id)
):
    """Get application status counts for a care request"""
    try:
        response = await make_supabase_request(
            "GET",
            "care_applications",
            params={"care_request_id": f"eq.{care_request_id}"}
        )
        
        if response.status_code == 200:
            applications = response.json()
            
            # Count applications by status
            status_counts = {}
            for app in applications:
                status = app.get("status", "pending")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Convert to list format
            result = [{"status": status, "count": count} for status, count in status_counts.items()]
            return result
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error fetching application status counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/user-applications")
async def get_user_applications(
    caregiver_user_id: str,
    user_id_from_token: str = Depends(get_authenticated_user_id)
):
    """Get all applications for a caregiver"""
    try:
        response = await make_supabase_request(
            "GET",
            "care_applications",
            params={"caregiver_user_id": f"eq.{caregiver_user_id}"}
        )
        
        if response.status_code == 200:
            applications = response.json()
            return [app["care_request_id"] for app in applications]
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error fetching user applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/check-application-limit")
async def check_application_limit(
    caregiver_user_id: str,
    user_id_from_token: str = Depends(get_authenticated_user_id)
):
    """Check if caregiver has reached application limit"""
    try:
        response = await make_supabase_request(
            "GET",
            "care_applications",
            params={
                "caregiver_user_id": f"eq.{caregiver_user_id}",
                "status": f"in.(pending,accepted,interview_scheduled)"
            }
        )
        
        if response.status_code == 200:
            applications = response.json()
            current_count = len(applications)
            limit_reached = current_count >= 3
            
            return {
                "limit_reached": limit_reached,
                "current_count": current_count,
                "max_limit": 3
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error checking application limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/apply-care-request")
async def apply_care_request(
    request: ApplyRequest,
    user_id_from_token: str = Depends(get_authenticated_user_id)
):
    """Apply for a care request"""
    try:
        # Check if already applied
        check_response = await make_supabase_request(
            "GET",
            "care_applications",
            params={
                "care_request_id": f"eq.{request.care_request_id}",
                "caregiver_user_id": f"eq.{request.user_id}"
            }
        )
        
        if check_response.status_code == 200:
            existing_applications = check_response.json()
            if existing_applications:
                return {"error": "You have already applied for this care request"}
        
        # Check application limit
        limit_response = await make_supabase_request(
            "GET",
            "care_applications",
            params={
                "caregiver_user_id": f"eq.{request.user_id}",
                "status": f"in.(pending,accepted,interview_scheduled)"
            }
        )
        
        if limit_response.status_code == 200:
            applications = limit_response.json()
            if len(applications) >= 3:
                return {"error": "You have reached the maximum of 3 applications"}
        
        # Create application
        application_data = {
            "care_request_id": request.care_request_id,
            "caregiver_user_id": request.user_id,
            "status": "pending"
        }
        
        response = await make_supabase_request(
            "POST",
            "care_applications",
            application_data
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error applying for care request: {e}")
        raise HTTPException(status_code=500, detail=str(e))