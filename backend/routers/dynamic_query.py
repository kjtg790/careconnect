# routers/dynamic_query.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Literal, Union
import asyncpg
import os
import jwt
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


class FilterCondition(BaseModel):
    column: str
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "like", "ilike", "in"]
    value: Union[str, int, float, List[str], List[int], None]


class QueryPayload(BaseModel):
    table: Optional[str] = None
    select: Optional[List[str]] = None
    filters: Optional[List[FilterCondition]] = None
    aggregates: Optional[List[Literal["count", "max", "min", "sum", "avg"]]] = None
    aggregate_column: Optional[str] = None
    raw_sql: Optional[str] = None  # Optional complete SQL

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)


@router.post("/query", tags=["Dynamic Query"])
async def execute_query(
    query_payload: QueryPayload,
    user_id: str = Depends(get_authenticated_user_id)
):
    if not query_payload.raw_sql and not query_payload.table:
        raise HTTPException(status_code=400, detail="Either raw_sql or table must be provided.")

    conn = await get_connection()
    try:
        if query_payload.raw_sql:
            sql = query_payload.raw_sql
            values = []
        else:
            # Build SQL dynamically
            table = query_payload.table
            select_columns = ", ".join(query_payload.select) if query_payload.select else "*"

            if query_payload.aggregates and query_payload.aggregate_column:
                agg_exprs = ", ".join([
                    f"{agg}({query_payload.aggregate_column}) AS {agg}_{query_payload.aggregate_column}"
                    for agg in query_payload.aggregates
                ])
                select_clause = agg_exprs
            else:
                select_clause = select_columns

            sql = f"SELECT {select_clause} FROM {table}"
            values = []

            if query_payload.filters:
                where_clauses = []
                for i, filt in enumerate(query_payload.filters):
                    if filt.operator == "in":
                        placeholders = ", ".join([f"${len(values) + j + 1}" for j in range(len(filt.value))])
                        clause = f"{filt.column} IN ({placeholders})"
                        values.extend(filt.value)
                    else:
                        clause = f"{filt.column} {filt.operator} ${len(values) + 1}"
                        values.append(filt.value)
                    where_clauses.append(clause)

                sql += " WHERE " + " AND ".join(where_clauses)

        # Execute SQL
        results = await conn.fetch(sql, *values)
        return [dict(record) for record in results]

    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL error: {str(e)}")
    finally:
        await conn.close()
