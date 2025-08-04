from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import os
import asyncpg
from auth.auth_utils import get_authenticated_user_id

router = APIRouter()
security = HTTPBearer()

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
    db_dsn = os.getenv("SUPABASE_DB")
    if not db_dsn:
        raise RuntimeError("SUPABASE_DB environment variable is not set")
    return await asyncpg.connect(dsn=db_dsn)

#-------------------Insert Daily Status Report ----------------------#
@router.post("/daily-status-reports/insert", tags=["Daily Status Reports"])
async def insert_daily_status_report(
    report: DailyStatusReportIn,
    caregiver_user_id: UUID = Depends(get_authenticated_user_id)
):
    conn = await get_connection()
    try:
        await conn.execute("""
            INSERT INTO daily_status_reports (
                id,
                care_service_id,
                caregiver_user_id,
                report_timestamp,
                health_report,
                mental_health_report,
                diet_routine,
                medicines_taken,
                other_notes
            )
            VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8
            )
        """,
        report.care_service_id,
        caregiver_user_id,
        report.report_timestamp,
        report.health_report,
        report.mental_health_report,
        report.diet_routine,
        report.medicines_taken,
        report.other_notes
        )
        return {"message": "Daily status report inserted"}
    finally:
        await conn.close()


# ------------------- Query Endpoint -------------------

@router.get("/daily-status-reports/query", response_model=List[DailyStatusReportOut], tags=["Daily Status Reports"])
async def query_daily_status_reports(
    user_id: UUID = Depends(get_authenticated_user_id),
    id: Optional[UUID] = Query(None),
    care_service_id: Optional[UUID] = Query(None),
    caregiver_user_id: Optional[UUID] = Query(None),
    report_timestamp: Optional[datetime] = Query(None),
    health_report: Optional[str] = Query(None),
    mental_health_report: Optional[str] = Query(None),
    diet_routine: Optional[str] = Query(None),
    medicines_taken: Optional[str] = Query(None),
    other_notes: Optional[str] = Query(None),
    created_at: Optional[datetime] = Query(None),
    updated_at: Optional[datetime] = Query(None),
):
    # Dynamic WHERE clause
    filters = ["caregiver_user_id = $1"]
    values = [user_id]
    idx = 2  # starting from $2 since $1 is user_id

    if id:
        filters.append(f"id = ${idx}")
        values.append(id)
        idx += 1
    if care_service_id:
        filters.append(f"care_service_id = ${idx}")
        values.append(care_service_id)
        idx += 1
    if caregiver_user_id:
        filters.append(f"caregiver_user_id = ${idx}")
        values.append(caregiver_user_id)
        idx += 1
    if report_timestamp:
        filters.append(f"report_timestamp = ${idx}")
        values.append(report_timestamp)
        idx += 1
    if health_report:
        filters.append(f"health_report ILIKE ${idx}")
        values.append(f"%{health_report}%")
        idx += 1
    if mental_health_report:
        filters.append(f"mental_health_report ILIKE ${idx}")
        values.append(f"%{mental_health_report}%")
        idx += 1
    if diet_routine:
        filters.append(f"diet_routine ILIKE ${idx}")
        values.append(f"%{diet_routine}%")
        idx += 1
    if medicines_taken:
        filters.append(f"medicines_taken ILIKE ${idx}")
        values.append(f"%{medicines_taken}%")
        idx += 1
    if other_notes:
        filters.append(f"other_notes ILIKE ${idx}")
        values.append(f"%{other_notes}%")
        idx += 1
    if created_at:
        filters.append(f"created_at::date = ${idx}")
        values.append(created_at.date())
        idx += 1
    if updated_at:
        filters.append(f"updated_at::date = ${idx}")
        values.append(updated_at.date())
        idx += 1

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"SELECT * FROM daily_status_reports {where_clause} ORDER BY report_timestamp DESC"

    conn = await get_connection()
    try:
        rows = await conn.fetch(query, *values)
        return [dict(row) for row in rows]
    finally:
        await conn.close()
