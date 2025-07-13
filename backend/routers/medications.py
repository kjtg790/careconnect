# routers/medications.py

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
DATABASE_URL = os.getenv("DATABASE_URL")

class MedicationCreate(BaseModel):
    health_profile_id: UUID
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None

class MedicationUpdate(BaseModel):
    id: UUID
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

@router.post("/insert", tags=["Medications"])
async def insert_medication(payload: MedicationCreate, user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        await conn.execute("""
            INSERT INTO public.medications (
                id, health_profile_id, name, dosage, frequency, timing
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5
            )
        """, payload.health_profile_id, payload.name, payload.dosage, payload.frequency, payload.timing)
        return {"message": "Medication inserted successfully"}
    finally:
        await conn.close()

@router.put("/update", tags=["Medications"])
async def update_medication(payload: MedicationUpdate, user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        result = await conn.fetchrow("SELECT id FROM public.medications WHERE id = $1", payload.id)
        if not result:
            raise HTTPException(status_code=404, detail="Medication not found")

        await conn.execute("""
            UPDATE public.medications
            SET
                dosage = COALESCE($2, dosage),
                frequency = COALESCE($3, frequency),
                timing = COALESCE($4, timing)
            WHERE id = $1
        """, payload.id, payload.dosage, payload.frequency, payload.timing)
        return {"message": "Medication updated successfully"}
    finally:
        await conn.close()

@router.get("/query", tags=["Medications"])
async def get_medications(user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        records = await conn.fetch("""
            SELECT m.*
            FROM public.medications m
            JOIN public.health_profiles h ON m.health_profile_id = h.id
            WHERE h.user_id = $1
            ORDER BY m.created_at DESC
        """, user_id)
        return [dict(r) for r in records]
    finally:
        await conn.close()
