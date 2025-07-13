# routers/session_routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
from auth.auth_utils import get_authenticated_user_id
from supabase_client import supabase
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()

# Environment-based config
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    data.update({"exp": expire, "type": "access"})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire, "type": "refresh"})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/api/auth/register", response_model=TokenResponse)
def register_user(user: UserRegister):
    # 1. Check if user exists
    existing = supabase.table("profiles").select("id").eq("email", user.email.lower()).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Register user in Supabase Auth
    auth_response = supabase.auth.admin.create_user({
        "email": user.email,
        "password": user.password,
        "email_confirm": True
    })
    if not auth_response or not auth_response.user:
        raise HTTPException(status_code=500, detail="Auth registration failed")

    user_id = auth_response.user["id"]

    # 3. Store profile
    supabase.table("profiles").insert({
        "id": user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "updated_at": datetime.utcnow()
    }).execute()

    # 4. Generate tokens
    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/api/auth/login", response_model=TokenResponse)
def login_user(user: UserLogin):
    # Supabase handles login via its auth system, but for custom password hashes:
    record = supabase.table("profiles").select("id, password_hash").eq("email", user.email.lower()).single().execute()
    if not record.data or not verify_password(user.password, record.data["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = record.data["id"]
    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
@router.post("/api/auth/logout", tags=["Auth"])
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(get_authenticated_user_id)):
    """Logout user by invalidating their session"""

    try:
        # Optional: Remove or revoke session server-side if required
        token = credentials.credentials

        # Supabase does not provide a direct API to invalidate JWTs.
        # If you're storing refresh tokens in a table, you can delete it here
        # Or, if you're using Supabase client on frontend, session is cleared there.

        return {"message": "Successfully logged out (client should discard token)"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )
