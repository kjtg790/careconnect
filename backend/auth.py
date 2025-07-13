from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import decode, PyJWKClient
import os

security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        jwks_url = f"{os.getenv('SUPABASE_URL')}/auth/v1/keys"
        jwk_client = PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(credentials.credentials)
        payload = decode(credentials.credentials, signing_key.key, algorithms=["RS256"])
        return payload["sub"]
    except Exception as e:
        print(f"JWT decode error: {str(e)}")  # Log error
        raise HTTPException(status_code=401, detail="Invalid JWT token")