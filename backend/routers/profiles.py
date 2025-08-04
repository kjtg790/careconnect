# routers/profiles.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
import asyncpg
import os
from auth.auth_utils import get_authenticated_user_id
import requests
router = APIRouter()
security = HTTPBearer()

DATABASE_URL = os.getenv("SUPABASE_DB")
SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Pydantic Models
class ProfileCreateUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class ProfileOut(ProfileCreateUpdate):
    id: UUID
    updated_at: Optional[datetime] = None


# DB Connection
async def get_connection():
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {str(e)}")


# Create or Update Profile
@router.post("/", response_model=ProfileOut, tags=["Profiles"])
async def create_or_update_profile(
    payload: ProfileCreateUpdate,
    user_id: str = Depends(get_authenticated_user_id),
):
    conn = await get_connection()
    try:
        result = await conn.fetchrow(
            """
            INSERT INTO public.profiles (
                id, updated_at, first_name, last_name, avatar_url, phone_number, address
            ) VALUES (
                $1, now(), $2, $3, $4, $5, $6
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = now(),
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                avatar_url = EXCLUDED.avatar_url,
                phone_number = EXCLUDED.phone_number,
                address = EXCLUDED.address
            RETURNING id, updated_at, first_name, last_name, avatar_url, phone_number, address
            """,
            user_id,
            payload.first_name,
            payload.last_name,
            payload.avatar_url,
            payload.phone_number,
            payload.address,
        )

        return {
            "id": str(result["id"]),
            "updated_at": result["updated_at"],
            "first_name": result["first_name"],
            "last_name": result["last_name"],
            "avatar_url": result["avatar_url"],
            "phone_number": result["phone_number"],
            "address": result["address"],
        }
    finally:
        await conn.close()


# ====== Query Profile ======

@router.get("/profiles/query", tags=["Profiles"])
def get_profile(
    profile_user_id: Optional[str] = Query(default=None),
    user_id: str = Depends(get_authenticated_user_id)
):
    target_id = profile_user_id or user_id
    url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{target_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
