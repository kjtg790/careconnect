from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
security = HTTPBearer()

def get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["RS256"])
        print("✅ JWT decoded:", payload)
        return payload.get("sub")
    except Exception as e:
        print("❌ JWT error:", e)
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/auth-check")
def test_auth(user_id: str = Depends(get_user)):
    return {"status": "authenticated", "user_id": user_id}
