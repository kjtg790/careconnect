# routers/direct_messages.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import asyncpg
from auth.auth_utils import get_authenticated_user_id

router = APIRouter()
security = HTTPBearer()

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# DB connection
async def get_connection():
    return await asyncpg.connect(dsn=os.getenv("SUPABASE_DB"))

# Request models
class DirectMessageCreate(BaseModel):
    receiver_id: str
    content: str

class DirectMessageUpdate(BaseModel):
    message_id: str
    content: str

class DirectMessageOut(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    created_at: datetime
    read_at: Optional[datetime]

# Create direct message
@router.post("/api/direct_messages/create", tags=["Direct Messages"])
async def create_direct_message(
    message: DirectMessageCreate,
    user_id: str = Depends(get_authenticated_user_id)
):
    conn = await get_connection()
    try:
        await conn.execute(
            """
            INSERT INTO public.direct_messages (
                id, sender_id, receiver_id, content
            ) VALUES (
                gen_random_uuid(), $1, $2, $3
            )
            """,
            user_id,
            message.receiver_id,
            message.content,
        )
        return {"message": "Message sent successfully"}
    finally:
        await conn.close()

# Update direct message content (only by sender)
@router.put("/api/direct_messages/update", tags=["Direct Messages"])
async def update_direct_message(
    update_data: DirectMessageUpdate,
    user_id: str = Depends(get_authenticated_user_id)
):
    conn = await get_connection()
    try:
        result = await conn.execute(
            """
            UPDATE public.direct_messages
            SET content = $1
            WHERE id = $2 AND sender_id = $3
            """,
            update_data.content,
            update_data.message_id,
            user_id
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Message not found or unauthorized")
        return {"message": "Message updated"}
    finally:
        await conn.close()

# Get all messages involving the logged-in user
@router.get("/api/direct_messages/query", tags=["Direct Messages"], response_model=List[DirectMessageOut])
async def get_direct_messages(user_id: str = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT id, sender_id, receiver_id, content, created_at, read_at
            FROM public.direct_messages
            WHERE sender_id = $1 OR receiver_id = $1
            ORDER BY created_at DESC
            """,
            user_id
        )

        # Properly convert UUID and datetime to expected str/datetime types
        return [
            {
                "id": str(row["id"]),
                "sender_id": str(row["sender_id"]),
                "receiver_id": str(row["receiver_id"]),
                "content": row["content"],
                "created_at": row["created_at"],  # datetime is accepted by Pydantic
                "read_at": row["read_at"] if row["read_at"] else None,
            }
            for row in rows
        ]
    finally:
        await conn.close()
