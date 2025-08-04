from fastapi import APIRouter, Query, HTTPException, Depends
import os
import psycopg2
from dotenv import load_dotenv
from auth.auth_utils import get_authenticated_user_id

load_dotenv()

router = APIRouter()


def get_connection():
    return psycopg2.connect(os.getenv("SUPABASE_DB"))


@router.get(
    "/enums",
    summary="Get ENUM values",
    description="Returns all ENUM types and their values, or a specific one if 'name' is passed"
)
def get_enum_values(
    name: str = Query(None, description="Optional enum type name"),
    user_id: str = Depends(get_authenticated_user_id)
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if name:
                # Return values for a specific enum type
                cur.execute("""
                    SELECT enumlabel
                    FROM pg_enum
                    JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
                    WHERE pg_type.typname = %s
                    ORDER BY enumsortorder
                """, (name,))
                values = [row[0] for row in cur.fetchall()]
                if not values:
                    raise HTTPException(status_code=404, detail=f"Enum type '{name}' not found.")
                return {name: values}
            else:
                # Return all enums in the public schema
                cur.execute("""
                    SELECT t.typname, e.enumlabel
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE n.nspname = 'public'
                    ORDER BY t.typname, e.enumsortorder
                """)
                enums = {}
                for typname, enumlabel in cur.fetchall():
                    enums.setdefault(typname, []).append(enumlabel)
                return enums
    finally:
        conn.close()
