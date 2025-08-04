from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from auth.auth_utils import get_authenticated_user_id
from supabase_client import supabase  # assumes you created this wrapper
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()

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

@router.post("/api/auth/register", response_model=TokenResponse)
def register_user(user: UserRegister):
    """Register user via Supabase Auth + create profile"""
    try:
        # 1. Create user via Supabase Auth (email/password or OAuth)
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })

        if not auth_response or not auth_response.session:
            raise HTTPException(status_code=500, detail="Supabase registration failed")

        user_id = auth_response.user["id"]

        # 2. Create user profile
        supabase.table("profiles").insert({
            "id": user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "updated_at": datetime.utcnow()
        }).execute()

        return TokenResponse(
            access_token=auth_response.session["access_token"],
            refresh_token=auth_response.session["refresh_token"],
            expires_in=auth_response.session["expires_in"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/api/auth/login", response_model=TokenResponse)
def login_user(user: UserLogin):
    """Login via Supabase Auth email/password or external provider"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })

        if not response or not response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return TokenResponse(
            access_token=response.session["access_token"],
            refresh_token=response.session["refresh_token"],
            expires_in=response.session["expires_in"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/api/auth/logout", tags=["Auth"])
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logs out the user from Supabase Auth (removes refresh token)"""

    try:
        token = credentials.credentials

        # Supabase client supports signOut() using REST if you store refresh tokens
        supabase.auth.sign_out()

        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )
