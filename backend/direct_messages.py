from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from auth.auth import get_user_id_from_jwt
from utils import make_supabase_request

router = APIRouter()

@router.post("/api/direct-messages")
async def send_direct_message(request: Request, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    data = await request.json()
    data["sender_id"] = user_id_from_token
    response = await make_supabase_request("POST", "direct_messages", data)
    if response.status_code == 201:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)

@router.get("/api/direct-messages")
async def get_direct_messages(user_id: str, other_user_id: Optional[str] = None, user_id_from_token: str = Depends(get_user_id_from_jwt)):
    # Fetch all messages between user_id and other_user_id, or all for user_id
    params = {"or": f"(and(sender_id.eq.{user_id},receiver_id.eq.{other_user_id}),and(sender_id.eq.{other_user_id},receiver_id.eq.{user_id}))"} if other_user_id else {"or": f"(sender_id.eq.{user_id},receiver_id.eq.{user_id})"}
    response = await make_supabase_request("GET", "direct_messages", params=params)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)