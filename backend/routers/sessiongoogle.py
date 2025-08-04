from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from jose import jwt, JWTError, ExpiredSignatureError
import os
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import secrets
import uuid

# --- Router & Security ---
router = APIRouter()
security = HTTPBearer()

# --- Config ---
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

GOOGLE_CLIENT_ID = os.getenv("SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

DATABASE_URL = os.getenv("SUPABASE_DB", "postgresql://user:password@localhost/dbname")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Models ---
class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

# --- DB Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Token Creation ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- JWT Verifier ---
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalid")

# --- Routes ---
@router.get("/api/auth/google/login")
async def google_login():
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return {"auth_url": auth_url, "state": state}

@router.get("/api/auth/google/callback")
async def google_callback(code: str, state: str, db=Depends(get_db)):
    try:
        token_info = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        ).json()
        access_token = token_info.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to fetch access token")

        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        email = user_info["email"]
        google_id = user_info["id"]
        first_name = user_info.get("given_name")
        last_name = user_info.get("family_name")
        avatar_url = user_info.get("picture")

        # Check existing profile
        result = db.execute(text("""
            SELECT id FROM profiles WHERE google_id = :google_id OR email = :email
        """), {"google_id": google_id, "email": email})
        user = result.fetchone()

        if user:
            user_id = user.id
        else:
            user_id = str(uuid.uuid4())

            # Insert into auth.users or supabase user management if applicable
            db.execute(text("""
                INSERT INTO users (id, email, created_at, updated_at)
                VALUES (:id, :email, NOW(), NOW())
            """), {"id": user_id, "email": email})

            db.execute(text("""
                INSERT INTO profiles (id, email, first_name, last_name, avatar_url, google_id, created_at, updated_at)
                VALUES (:id, :email, :first_name, :last_name, :avatar_url, :google_id, NOW(), NOW())
            """), {
                "id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "avatar_url": avatar_url,
                "google_id": google_id
            })

        db.commit()

        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})

        return RedirectResponse(f"{FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(user_id: str = Depends(verify_token), db=Depends(get_db)):
    result = db.execute(text("""
        SELECT id, email, first_name, last_name, phone_number, avatar_url, google_id
        FROM profiles WHERE id = :id
    """), {"id": user_id})
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user._mapping)

@router.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db=Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})

        result = db.execute(text("""
            SELECT id, email, first_name, last_name, phone_number, avatar_url, google_id
            FROM profiles WHERE id = :id
        """), {"id": user_id})
        user = result.fetchone()

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user._mapping)
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/api/auth/logout")
async def logout_user(user_id: str = Depends(verify_token)):
    return {"message": "Successfully logged out"}
