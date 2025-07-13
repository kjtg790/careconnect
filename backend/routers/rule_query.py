# routers/rule_query.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncpg
import os
import jwt
from auth.auth_utils import get_authenticated_user_id

router = APIRouter()
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
DATABASE_URL = os.getenv("SUPABASE_DB_URL")

class RuleQueryInput(BaseModel):
    rule_name: str
    parameters: Dict[str, Any] = {}

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

def get_current_user_id():
    # Dummy for now. Replace with JWT extraction logic.
    return "mock-user-id"

@router.post("/rules/execute", tags=["Rule Engine"])
async def execute_rule(input: RuleQueryInput, user_id=Depends(get_authenticated_user_id)):
    conn = await get_connection()
    try:
        rule = await conn.fetchrow("SELECT * FROM rules WHERE name = $1", input.rule_name)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        table = rule["table_name"]
        select_clause = ""
        values = []
        param_index = 1

        # Build SELECT clause
        if rule["aggregates"]:
            aggregates = []
            for agg in rule["aggregates"]:
                f = agg["function"]
                col = agg["column"]
                alias = agg["alias"]
                aggregates.append(f"{f}({col}) AS {alias}")
            select_clause = ", ".join(aggregates)
        else:
            select_clause = ", ".join(rule["allowed_columns"])

        sql = f"SELECT {select_clause} FROM {table}"

        # WHERE clause
        where_clause = []
        if rule["where_template"]:
            for cond in rule["where_template"]:
                param_val = input.parameters.get(cond["param"])
                if param_val is None:
                    raise HTTPException(status_code=400, detail=f"Missing param: {cond['param']}")
                where_clause.append(f"{cond['column']} {cond['operator']} ${param_index}")
                values.append(param_val)
                param_index += 1
            sql += " WHERE " + " AND ".join(where_clause)

        if rule["group_by"]:
            sql += " GROUP BY " + ", ".join(rule["group_by"])

        results = await conn.fetch(sql, *values)
        return [dict(row) for row in results]

    finally:
        await conn.close()
