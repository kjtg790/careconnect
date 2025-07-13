# routers/user_roles_util.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from config import settings
import asyncpg
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()

# Use DB URL from config
DATABASE_URL = settings.SUPABASE_DB

# Pydantic model for response
class UserRoleOut(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    created_at: datetime

# Simple function to get DB connection
async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

# Dependency to extract user_id from JWT manually (can be refined later)
async def get_user_id_from_token():
    # This can be enhanced to extract JWT from header and decode it
    return "placeholder-user-id"  # Replace with actual logic if needed

@router.get("/api/user-roles", response_model=List[UserRoleOut], tags=["User Roles"])
async def get_user_roles(
    user_id: str = Query(..., description="User ID to get roles for"),
    user_id_from_token: str = Depends(get_authenticated_user_id)
):
    """
    Get user roles for a specific user from `user_roles` table.
    """
    try:
        conn = await get_connection()
        records = await conn.fetch(
            "SELECT id, user_id, role, created_at FROM user_roles WHERE user_id = $1",
            user_id
        )
        await conn.close()
        return [dict(r) for r in records]
    except Exception as e:
        print(f"❌ Error fetching user roles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
