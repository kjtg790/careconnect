# routers/health_reports.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import os
import jwt
import asyncpg
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

class HealthReportCreate(BaseModel):
    health_profile_id: UUID
    file_name: str
    storage_path: str
    caption: Optional[str]

class HealthReportUpdate(BaseModel):
    id: UUID
    caption: Optional[str]
    file_name: Optional[str]
    storage_path: Optional[str]


async def get_connection():
    return await asyncpg.connect(os.getenv("DATABASE_URL"))

@router.post("/insert", tags=["Health Reports"])
async def insert_health_report(report: HealthReportCreate, user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        await conn.execute("""
            INSERT INTO public.health_reports (
                id, health_profile_id, file_name, storage_path, caption, uploader_user_id
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5
            )
        """, report.health_profile_id, report.file_name, report.storage_path, report.caption, user_id)
        return {"message": "Health report inserted successfully"}
    finally:
        await conn.close()

@router.put("/update", tags=["Health Reports"])
async def update_health_report(update: HealthReportUpdate, user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        existing = await conn.fetchrow("SELECT uploader_user_id FROM public.health_reports WHERE id = $1", update.id)
        if not existing:
            raise HTTPException(status_code=404, detail="Report not found")
        if existing["uploader_user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")

        await conn.execute("""
            UPDATE public.health_reports
            SET
                file_name = COALESCE($2, file_name),
                storage_path = COALESCE($3, storage_path),
                caption = COALESCE($4, caption)
            WHERE id = $1
        """, update.id, update.file_name, update.storage_path, update.caption)
        return {"message": "Health report updated"}
    finally:
        await conn.close()

@router.get("/query", tags=["Health Reports"])
async def query_health_reports(user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        records = await conn.fetch("""
            SELECT * FROM public.health_reports
            WHERE uploader_user_id = $1
            ORDER BY created_at DESC
        """, user_id)
        return [dict(r) for r in records]
    finally:
        await conn.close()
