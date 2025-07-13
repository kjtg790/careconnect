from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from auth.auth import get_user_id_from_jwt
from utils import make_supabase_request

router = APIRouter()

@router.post("/api/reference-requests")
async def send_reference_request(request: Request, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    data = await request.json()
    data["requester_id"] = user_id_from_token
    response = await make_supabase_request("POST", "reference_requests", data)
    if response.status_code == 201:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)

@router.post("/api/reference-responses")
async def submit_reference_response(request: Request, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    data = await request.json()
    data["responder_id"] = user_id_from_token
    response = await make_supabase_request("POST", "reference_responses", data)
    if response.status_code == 201:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)

@router.get("/api/references")
async def get_references(user_id: str, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    params = {"user_id": f"eq.{user_id}"}
    response = await make_supabase_request("GET", "references", params=params)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)