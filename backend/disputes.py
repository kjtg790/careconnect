from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from auth.auth import get_user_id_from_jwt
from utils import make_supabase_request

router = APIRouter()

@router.post("/api/disputes")
async def create_dispute(request: Request, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    data = await request.json()
    data["created_by"] = user_id_from_token
    response = await make_supabase_request("POST", "disputes", data)
    if response.status_code == 201:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)

@router.get("/api/disputes")
async def get_disputes(user_id: Optional[str] = None, care_request_id: Optional[str] = None, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    params = {}
    if user_id:
        params["created_by"] = f"eq.{user_id}"
    if care_request_id:
        params["care_request_id"] = f"eq.{care_request_id}"
    response = await make_supabase_request("GET", "disputes", params=params)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)

@router.patch("/api/disputes/{dispute_id}")
async def update_dispute(dispute_id: str, request: Request, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    data = await request.json()
    response = await make_supabase_request("PATCH", f"disputes?id=eq.{dispute_id}", data)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)