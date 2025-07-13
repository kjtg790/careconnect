from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from auth.auth import get_user_id_from_jwt
from utils import make_supabase_request

router = APIRouter()

@router.get("/api/profiles")
async def get_profiles(
    ids: Optional[str] = Query(None, description="Comma-separated list of user IDs"),
    user_id_from_token: str = Depends(get_user_id_from_jwt)
):
    """
    Fetch user profiles by a comma-separated list of IDs.
    Example: /api/profiles?ids=uuid1,uuid2,uuid3
    """
    if not ids:
        raise HTTPException(status_code=400, detail="No ids provided")
    id_list = ids.split(",")
    params = {"id": f"in.({','.join(id_list)})"}
    response = await make_supabase_request("GET", "profiles", params=params)
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail=response.text)