from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import os
import uuid
from auth.auth_utils import get_authenticated_user_id
import supabase

router = APIRouter()
security = HTTPBearer()

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_DB_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_BUCKET", "agreements")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase environment variables are not set properly.")

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def to_serializable(data: dict) -> dict:
    """Convert date/datetime objects to ISO 8601 strings."""
    for key, value in data.items():
        if isinstance(value, (date, datetime)):
            data[key] = value.isoformat()
    return data


class AgreementBase(BaseModel):
    caregiver_user_id: str
    care_seeker_user_id: str
    care_request_id: str
    care_application_id: str
    agent_id: Optional[str] = None
    start_date: date
    end_date: date
    expiry_date: Optional[date] = None
    signed_on: Optional[datetime] = None
    agreement_link: Optional[str] = None


class AgreementCreate(AgreementBase):
    pass


class AgreementUpdate(BaseModel):
    id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    expiry_date: Optional[date] = None
    signed_on: Optional[datetime] = None
    agreement_link: Optional[str] = None


@router.post("/agreements", dependencies=[Depends(security)])
def create_agreement(agreement: AgreementCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = get_authenticated_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = agreement.dict()
    data["created_on"] = datetime.utcnow()
    data = to_serializable(data)

    response = supabase_client.table("agreements").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create agreement")

    return {"message": "Agreement created successfully", "data": response.data}


@router.put("/agreements", dependencies=[Depends(security)])
def update_agreement(agreement: AgreementUpdate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = get_authenticated_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    update_data = {k: v for k, v in agreement.dict().items() if v is not None and k != "id"}
    update_data = to_serializable(update_data)

    response = supabase_client.table("agreements").update(update_data).eq("id", agreement.id).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update agreement")

    return {"message": "Agreement updated successfully", "data": response.data}


@router.get("/agreements", dependencies=[Depends(security)])
def list_agreements(care_seeker_user_id: Optional[str] = None, caregiver_user_id: Optional[str] = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = get_authenticated_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    query = supabase_client.table("agreements").select("*")

    if care_seeker_user_id:
        query = query.eq("care_seeker_user_id", care_seeker_user_id)
    if caregiver_user_id:
        query = query.eq("caregiver_user_id", caregiver_user_id)

    response = query.execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="No agreements found")

    return {"agreements": response.data}
