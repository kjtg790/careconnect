# routers/caregiver_reviews.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from config import settings
import jwt
import requests
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()

SUPABASE_URL = settings.SUPABASE_DB_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
JWT_SECRET = settings.SUPABASE_JWT_SECRET

# ======= Models =======

class CaregiverReviewInsert(BaseModel):
    caregiver_user_id: str
    rating: int
    review_text: Optional[str] = None

class CaregiverReviewUpdate(BaseModel):
    id: str
    rating: Optional[int] = None
    review_text: Optional[str] = None

class CaregiverReview(BaseModel):
    id: str
    caregiver_user_id: str
    reviewer_user_id: str
    rating: int
    review_text: Optional[str]


# ======= Insert =======

@router.post("/caregiver_reviews/insert", tags=["Caregiver Reviews"])
def insert_review(
    payload: CaregiverReviewInsert,
    reviewer_user_id: str = Depends(get_authenticated_user_id)
):
    if payload.caregiver_user_id == reviewer_user_id:
        raise HTTPException(status_code=400, detail="Reviewer cannot be the caregiver")

    url = f"{SUPABASE_URL}/rest/v1/caregiver_reviews"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = payload.dict()
    data["reviewer_user_id"] = reviewer_user_id

    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Review added", "data": response.json()}

# ======= Update =======

@router.put("/caregiver_reviews/update", tags=["Caregiver Reviews"])
def update_review(
    payload: CaregiverReviewUpdate,
    reviewer_user_id: str = Depends(get_authenticated_user_id)
):
    url = f"{SUPABASE_URL}/rest/v1/caregiver_reviews?id=eq.{payload.id}&reviewer_user_id=eq.{reviewer_user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    data = {k: v for k, v in payload.dict().items() if v is not None}

    response = requests.patch(url, json=data, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Review updated", "data": response.json()}

# ======= Query (Get My Submitted Reviews) =======

@router.get("/caregiver_reviews/query", tags=["Caregiver Reviews"], response_model=List[CaregiverReview])
def query_my_reviews(reviewer_user_id: str = Depends(get_authenticated_user_id)):
    url = f"{SUPABASE_URL}/rest/v1/caregiver_reviews?reviewer_user_id=eq.{reviewer_user_id}&select=*"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
