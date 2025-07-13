# auth/auth_utils.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from jwt import decode, PyJWKClient
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
security = HTTPBearer()

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import jwt

security = HTTPBearer()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
print(SUPABASE_JWT_SECRET);
def get_authenticated_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        token = credentials.credentials

        # Decode using HS256 (HMAC) with Supabase JWT secret
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"],audience="authenticated")

        print("✅ JWT Decoded:", payload)
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        print("❌ JWT Decode Error:", str(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")

