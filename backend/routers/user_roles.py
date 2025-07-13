# routers/user_roles.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncpg
import os
import jwt
from uuid import UUID
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()

DATABASE_URL = os.getenv("SUPABASE_DB")
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


class UserRoleIn(BaseModel):
    role: str  # Ensure this aligns with your public.app_role enum


class UserRoleOut(UserRoleIn):
    id: UUID
    user_id: UUID
    role: str
    created_at: datetime

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)


@router.post("/", response_model=UserRoleOut, tags=["User Roles"])
async def add_user_role(
    role_data: UserRoleIn,
    user_id: str = Depends(get_authenticated_user_id),
):
    conn = await get_connection()
    try:
        result = await conn.fetchrow(
            """
            INSERT INTO public.user_roles (user_id, role, created_at)
            VALUES ($1, $2, timezone('utc', now()))
            ON CONFLICT (user_id, role) DO NOTHING
            RETURNING *
            """,
            user_id,
            role_data.role
        )
        if not result:
            raise HTTPException(status_code=400, detail="Role already assigned to user.")
        return result
    finally:
        await conn.close()


@router.get("/", response_model=List[UserRoleOut], tags=["User Roles"])
async def get_user_roles(
    user_id: str = Depends(get_authenticated_user_id),
):
    conn = await get_connection()
    try:
        results = await conn.fetch(
            "SELECT * FROM public.user_roles WHERE user_id = $1",
            user_id
        )
        return results
    finally:
        await conn.close()


@router.put("/", response_model=UserRoleOut, tags=["User Roles"])
async def update_user_role(
    role_data: UserRoleIn,
    user_id: str = Depends(get_authenticated_user_id)
):
    conn = await get_connection()
    try:
        # There is no natural way to update "role" in composite unique key without deleting/reinserting.
        result = await conn.fetchrow(
            """
            UPDATE public.user_roles
            SET role = $2
            WHERE user_id = $1
            RETURNING *
            """,
            user_id,
            role_data.role
        )
        if not result:
            raise HTTPException(status_code=404, detail="No role found to update.")
        return result
    finally:
        await conn.close()
