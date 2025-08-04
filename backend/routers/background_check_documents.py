# routers/background_check_documents.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt
import requests
from config import settings
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()

SUPABASE_URL = settings.SUPABASE_DB_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
JWT_SECRET = settings.SUPABASE_JWT_SECRET

# ======= Pydantic Models =======

class BackgroundDocumentInsert(BaseModel):
    document_type: str
    file_name: str
    storage_path: str
    status: Optional[str] = None
class BackgroundDocumentUpdate(BaseModel):
    document_type: Optional[str] = None
    file_name: Optional[str] = None
    storage_path: Optional[str] = None
    status: Optional[str] = None
class BackgroundDocumentResponse(BaseModel):
    id: str
    user_id: str
    document_type: str
    file_name: str
    storage_path: str
    status: Optional[str] = None
# ======= Insert =======

@router.post("/background-check-documents/insert", tags=["Background Check Documents"])
def insert_document(payload: BackgroundDocumentInsert, user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/background_check_documents"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = payload.dict()
    data["user_id"] = user_id

    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Document inserted", "data": response.json()}

# ======= Update =======

@router.put("/background-check-documents/update", tags=["Background Check Documents"])
def update_document(payload: BackgroundDocumentUpdate, user_id: str = Depends(get_authenticated_user_id)):
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    url = f"{SUPABASE_URL}/rest/v1/background_check_documents?user_id=eq.{user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    response = requests.patch(url, json=update_data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Document updated", "data": response.json()}

# ======= Query =======

@router.get("/background-check-documents/query", tags=["Background Check Documents"], response_model=list[BackgroundDocumentResponse])
def get_documents(user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/background_check_documents?user_id=eq.{user_id}&select=*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
