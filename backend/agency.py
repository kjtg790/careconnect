from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from auth.auth import get_user_id_from_jwt
from utils import make_supabase_request

router = APIRouter()

@router.post("/api/agency-registration")
async def register_agency(request: Request, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    data = await request.json()
    data["user_id"] = user_id_from_token
    response = await make_supabase_request("POST", "agencies", data)
    if response.status_code == 201:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)

@router.get("/api/agencies")
async def get_agencies(user_id: Optional[str] = None, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    params = {}
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    response = await make_supabase_request("GET", "agencies", params=params)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)

@router.patch("/api/agencies/{agency_id}")
async def update_agency(agency_id: str, request: Request, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    data = await request.json()
    response = await make_supabase_request("PATCH", f"agencies?id=eq.{agency_id}", data)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)