from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import httpx
import os
import jwt
from dotenv import load_dotenv

load_dotenv()

# 🔐 JWT and Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Ensure env vars are loaded for debugging
print(f"DEBUG: SUPABASE_URL loaded: {bool(SUPABASE_URL)}")
print(f"DEBUG: SUPABASE_SERVICE_ROLE_KEY loaded: {bool(SUPABASE_SERVICE_ROLE_KEY)}")
print(f"DEBUG: SUPABASE_JWT_SECRET loaded: {bool(SUPABASE_JWT_SECRET)}")


# 🔐 HTTP Bearer security scheme
security = HTTPBearer()
update_interview_router = APIRouter()

# 📦 Request model
class InterviewUpdateRequest(BaseModel):
    id: str
    message: Optional[str] = None
    status: Optional[str] = None
    outcome_status: Optional[str] = None
    feedback: Optional[str] = None
    scheduled_date_time: Optional[datetime] = None

# ✅ Auth extractor
def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        user_id = decoded.get("sub")
        print(f"✅ JWT Decoded inside auth module: {decoded}") # Changed to show full decoded token
        print(f"✅ Authenticated User ID: {user_id}")
        return user_id
    except Exception as e:
        print("❌ JWT Decode Error:", str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

@update_interview_router.put("/api/update-interview")
async def update_interview(
    payload: InterviewUpdateRequest,
    user_id: str = Depends(get_user_id)
):
    print(f"DEBUG: Inside update_interview function for user_id: {user_id}")
    print(f"DEBUG: Received payload: {payload.dict()}")

    try:
        # Attempt to access a field from payload that might trigger an error if payload is malformed
        test_id = payload.id
        print(f"DEBUG: Successfully accessed payload.id: {test_id}")

        # Return a simple success to confirm function entry
        return {"message": "Received payload and user_id successfully", "user_id": user_id, "payload_id": test_id}

    except Exception as e:
        print(f"🔥 CRITICAL ERROR IN update_interview: {e}")
        import traceback
        traceback.print_exc() # Print full traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unhandled error occurred: {e}")