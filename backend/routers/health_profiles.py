# routers/health_profiles.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, conlist
from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
import os
import jwt
import asyncpg
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

class HealthProfileBase(BaseModel):
    date_of_birth: Optional[date]
    gender: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    waist_circumference_cm: Optional[float]
    shirt_size: Optional[str]
    blood_group: Optional[str]
    blood_pressure_systolic: Optional[int]
    blood_pressure_diastolic: Optional[int]
    fasting_glucose: Optional[float]
    postprandial_glucose: Optional[float]
    cholesterol_total: Optional[float]
    oxygen_saturation: Optional[float]
    pre_existing_conditions: Optional[List[str]]
    allergies: Optional[List[str]]
    recent_surgeries: Optional[List[str]]
    diet_routine: Optional[Dict[str, Any]]
    diet_preferences: Optional[List[str]]
    current_exercise_routine: Optional[Dict[str, Any]]
    preferred_exercises: Optional[List[str]]
    ai_insights: Optional[str]

class HealthProfileCreate(HealthProfileBase):
    pass

class HealthProfileUpdate(HealthProfileBase):
    pass


async def get_connection():
    return await asyncpg.connect(os.getenv("DATABASE_URL"))

@router.post("/insert", tags=["Health Profiles"])
async def insert_health_profile(profile: HealthProfileCreate, user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        await conn.execute("""
            INSERT INTO public.health_profiles (
                id, user_id, date_of_birth, gender, height_cm, weight_kg, waist_circumference_cm,
                shirt_size, blood_group, blood_pressure_systolic, blood_pressure_diastolic,
                fasting_glucose, postprandial_glucose, cholesterol_total, oxygen_saturation,
                pre_existing_conditions, allergies, recent_surgeries, diet_routine, diet_preferences,
                current_exercise_routine, preferred_exercises, ai_insights
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, $6,
                $7, $8, $9, $10,
                $11, $12, $13, $14,
                $15, $16, $17, $18, $19,
                $20, $21, $22
            )
        """, user_id, profile.date_of_birth, profile.gender, profile.height_cm, profile.weight_kg, profile.waist_circumference_cm,
             profile.shirt_size, profile.blood_group, profile.blood_pressure_systolic, profile.blood_pressure_diastolic,
             profile.fasting_glucose, profile.postprandial_glucose, profile.cholesterol_total, profile.oxygen_saturation,
             profile.pre_existing_conditions, profile.allergies, profile.recent_surgeries, profile.diet_routine,
             profile.diet_preferences, profile.current_exercise_routine, profile.preferred_exercises, profile.ai_insights)
        return {"message": "Health profile created"}
    finally:
        await conn.close()

@router.put("/update", tags=["Health Profiles"])
async def update_health_profile(profile: HealthProfileUpdate, user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        await conn.execute("""
            UPDATE public.health_profiles SET
                date_of_birth=$2,
                gender=$3,
                height_cm=$4,
                weight_kg=$5,
                waist_circumference_cm=$6,
                shirt_size=$7,
                blood_group=$8,
                blood_pressure_systolic=$9,
                blood_pressure_diastolic=$10,
                fasting_glucose=$11,
                postprandial_glucose=$12,
                cholesterol_total=$13,
                oxygen_saturation=$14,
                pre_existing_conditions=$15,
                allergies=$16,
                recent_surgeries=$17,
                diet_routine=$18,
                diet_preferences=$19,
                current_exercise_routine=$20,
                preferred_exercises=$21,
                ai_insights=$22
            WHERE user_id=$1
        """, user_id, profile.date_of_birth, profile.gender, profile.height_cm, profile.weight_kg, profile.waist_circumference_cm,
             profile.shirt_size, profile.blood_group, profile.blood_pressure_systolic, profile.blood_pressure_diastolic,
             profile.fasting_glucose, profile.postprandial_glucose, profile.cholesterol_total, profile.oxygen_saturation,
             profile.pre_existing_conditions, profile.allergies, profile.recent_surgeries, profile.diet_routine,
             profile.diet_preferences, profile.current_exercise_routine, profile.preferred_exercises, profile.ai_insights)
        return {"message": "Health profile updated"}
    finally:
        await conn.close()

@router.get("/query", tags=["Health Profiles"])
async def get_health_profile(user_id: UUID = Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM public.health_profiles WHERE user_id = $1", user_id)
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")
        return dict(row)
    finally:
        await conn.close()
