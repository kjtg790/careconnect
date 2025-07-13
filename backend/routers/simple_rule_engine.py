# routers/simple_rule_engine.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from config import settings
from uuid import UUID
import jwt
import asyncpg
from auth.auth_utils import get_authenticated_user_id

router = APIRouter()
security = HTTPBearer()

# ENV variables
JWT_SECRET = settings.SUPABASE_JWT_SECRET
SUPABASE_DB_URL = settings.SUPABASE_DB_URL
SUPABASE_DB = settings.SUPABASE_DB
SUPABASE_DB_POOL = None  # Initialized in lifespan event

class RuleEngineBase(BaseModel):
    name: str
    table_name: str
    condition_sql: str
    error_message: str
    is_active: Optional[bool] = True

class RuleEngineUpdate(BaseModel):
    name: str
    table_name: Optional[str] = None
    condition_sql: Optional[str] = None
    error_message: Optional[str] = None
    is_active: Optional[bool] = None

class RuleEngineOut(RuleEngineBase):
    id: UUID

class RuleExecuteRequest(BaseModel):
    rule_name: str
    parameters: Dict[str, Any]  # e.g., {"user_id": "uuid-string"}

@router.on_event("startup")
async def startup():
    global SUPABASE_DB_POOL
    SUPABASE_DB_POOL = await asyncpg.create_pool(SUPABASE_DB)

@router.post("/rules_engine", response_model=RuleEngineOut, tags=["Simple Rule Engine"])
async def create_rule(rule: RuleEngineBase, user_id: str = Depends(get_authenticated_user_id
)):
    async with SUPABASE_DB_POOL.acquire() as conn:
        try:
            result = await conn.fetchrow("""
                INSERT INTO rules_engine (name, table_name, condition_sql, error_message, is_active)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *;
            """, rule.name, rule.table_name, rule.condition_sql, rule.error_message, rule.is_active)
            return dict(result)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Rule with this name already exists")

@router.put("/rules_engine/{name}", response_model=RuleEngineOut, tags=["Simple Rule Engine"])
async def update_rule(name: str, update: RuleEngineUpdate, user_id: str = Depends(get_authenticated_user_id
)):
    async with SUPABASE_DB_POOL.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM rules_engine WHERE name = $1", name)
        if not existing:
            raise HTTPException(status_code=404, detail="Rule not found")
        updated = {
            **dict(existing),
            **{k: v for k, v in update.dict().items() if v is not None}
        }
        result = await conn.fetchrow("""
            UPDATE rules_engine SET
                table_name = $1,
                condition_sql = $2,
                error_message = $3,
                is_active = $4
            WHERE name = $5
            RETURNING *;
        """, updated["table_name"], updated["condition_sql"], updated["error_message"], updated["is_active"], name)
        return dict(result)

@router.get("/rules_engine", response_model=List[RuleEngineOut], tags=["Simple Rule Engine"])
async def list_rules(user_id: str = Depends(get_authenticated_user_id
)):
    async with SUPABASE_DB_POOL.acquire() as conn:
        records = await conn.fetch("SELECT * FROM rules_engine ORDER BY name")
        return [dict(row) for row in records]

@router.get("/rules_engine/{name}", response_model=RuleEngineOut, tags=["Simple Rule Engine"])
async def get_rule_by_name(name: str, user_id: str = Depends(get_authenticated_user_id
)):
    async with SUPABASE_DB_POOL.acquire() as conn:
        record = await conn.fetchrow("SELECT * FROM rules_engine WHERE name = $1", name)
        if not record:
            raise HTTPException(status_code=404, detail="Rule not found")
        return dict(record)

@router.post("/rules_engine/execute", tags=["Simple Rule Engine"])
async def execute_rule(
    payload: RuleExecuteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        token = credentials.credentials
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["RS256"])
        user_id = decoded_token.get("sub")

        async with SUPABASE_DB_POOL.acquire() as conn:
            rule = await conn.fetchrow("""
                SELECT * FROM rules_engine
                WHERE name = $1 AND is_active = TRUE
            """, payload.rule_name)

            if not rule:
                raise HTTPException(status_code=404, detail="Rule not found or inactive.")

            condition_sql = rule["condition_sql"]
            error_message = rule["error_message"]

            # Dynamically pass parameters
            param_values = list(payload.parameters.values())

            result = await conn.fetchval(condition_sql, *param_values)

            if isinstance(result, int) and result > 3:
                return {"status": "error", "message": error_message}

            return {"status": "success", "message": "Rule passed", "result": result}

    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
