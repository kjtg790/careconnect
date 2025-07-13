from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from auth.auth import get_user_id_from_jwt
from utils import make_supabase_request

router = APIRouter()

@router.get("/api/caregiver-profiles")
async def get_caregiver_profile(
    user_id: str,
    user_id_from_token: str = Depends(get_user_id_from_jwt)
):
    """Get caregiver profile by user ID"""
    try:
        response = await make_supabase_request(
            "GET",
            "caregiver_profiles",
            params={"user_id": f"eq.{user_id}"}
        )
        
        if response.status_code == 200:
            profiles = response.json()
            return profiles[0] if profiles else None
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error fetching caregiver profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/caregiver-profiles")
async def create_caregiver_profile(
    request: Request,
    user_id_from_token: str = Depends(get_user_id_from_jwt)
):
    """Create a new caregiver profile"""
    try:
        data = await request.json()
        
        # Check if profile already exists
        check_response = await make_supabase_request(
            "GET",
            "caregiver_profiles",
            params={"user_id": f"eq.{data['user_id']}"}
        )
        
        if check_response.status_code == 200:
            existing_profiles = check_response.json()
            if existing_profiles:
                raise HTTPException(status_code=409, detail="Profile already exists")
        
        response = await make_supabase_request(
            "POST",
            "caregiver_profiles",
            data
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error creating caregiver profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/api/caregiver-profiles")
async def update_caregiver_profile(
    request: Request,
    user_id_from_token: str = Depends(get_user_id_from_jwt)
):
    """Update an existing caregiver profile"""
    try:
        data = await request.json()
        
        response = await make_supabase_request(
            "PATCH",
            f"caregiver_profiles?user_id=eq.{data['user_id']}",
            data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        print(f"❌ Error updating caregiver profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))