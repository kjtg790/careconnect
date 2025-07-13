# routers/profiles.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
import asyncpg
import os
from auth.auth_utils import get_authenticated_user_id

router = APIRouter()
security = HTTPBearer()

DATABASE_URL = os.getenv("SUPABASE_DB")


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


# Get Profile
@router.get("/api/profile", response_model=ProfileOut, tags=["Profiles"])
async def get_profile(user_id: str = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT id, updated_at, first_name, last_name, avatar_url, phone_number, address
            FROM public.profiles
            WHERE id = $1
            """,
            user_id
        )

        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")

        return {
            "id": str(row["id"]),
            "updated_at": row["updated_at"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "avatar_url": row["avatar_url"],
            "phone_number": row["phone_number"],
            "address": row["address"],
        }

    finally:
        await conn.close()
