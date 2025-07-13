# daily_status_reports.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import os
import asyncpg
import jwt
from auth.auth_utils import get_authenticated_user_id
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# ------------------- Models -------------------

class DailyStatusReportIn(BaseModel):
    care_service_id: UUID
    report_timestamp: datetime
    health_report: Optional[str] = None
    mental_health_report: Optional[str] = None
    diet_routine: Optional[str] = None
    medicines_taken: Optional[str] = None
    other_notes: Optional[str] = None

class DailyStatusReportOut(DailyStatusReportIn):
    id: UUID
    caregiver_user_id: UUID
    created_at: datetime
    updated_at: datetime

# ------------------- DB Connection -------------------

async def get_connection():
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432))
    )

# ------------------- API Endpoints -------------------

@router.post("/daily-status-reports/insert", response_model=DailyStatusReportOut, tags=["Daily Status Reports"])
async def insert_daily_status_report(
    report: DailyStatusReportIn,
    user_id: UUID = Depends(get_authenticated_user_id)
):
    query = """
        INSERT INTO daily_status_reports (
            care_service_id,
            caregiver_user_id,
            report_timestamp,
            health_report,
            mental_health_report,
            diet_routine,
            medicines_taken,
            other_notes
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query, report.care_service_id, user_id,
                                  report.report_timestamp, report.health_report,
                                  report.mental_health_report, report.diet_routine,
                                  report.medicines_taken, report.other_notes)
        return dict(row)
    finally:
        await conn.close()


@router.put("/daily-status-reports/update", response_model=DailyStatusReportOut, tags=["Daily Status Reports"])
async def update_daily_status_report(
    report_id: UUID,
    report: DailyStatusReportIn,
    user_id: UUID = Depends(get_authenticated_user_id)
):
    query = """
        UPDATE daily_status_reports
        SET
            care_service_id = $1,
            report_timestamp = $2,
            health_report = $3,
            mental_health_report = $4,
            diet_routine = $5,
            medicines_taken = $6,
            other_notes = $7,
            updated_at = now()
        WHERE id = $8 AND caregiver_user_id = $9
        RETURNING *
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(query,
            report.care_service_id,
            report.report_timestamp,
            report.health_report,
            report.mental_health_report,
            report.diet_routine,
            report.medicines_taken,
            report.other_notes,
            report_id,
            user_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        return dict(row)
    finally:
        await conn.close()


@router.get("/daily-status-reports/query", response_model=List[DailyStatusReportOut], tags=["Daily Status Reports"])
async def query_daily_status_reports(user_id: UUID = Depends(get_authenticated_user_id)):
    query = """
        SELECT * FROM daily_status_reports
        WHERE caregiver_user_id = $1
        ORDER BY report_timestamp DESC
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch(query, user_id)
        return [dict(row) for row in rows]
    finally:
        await conn.close()
