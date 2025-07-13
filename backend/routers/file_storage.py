# routers/file_storage.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_403_FORBIDDEN
import httpx
import os
from datetime import datetime
import uuid
from io import BytesIO
from auth.auth_utils import get_authenticated_user_id
router = APIRouter()
security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "background-check-documents"
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/api/background-check-documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    user_id: str = Depends(get_authenticated_user_id)
):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # Create a unique file path: <user_id>/<timestamp>_<uuid>_<original_filename>
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{timestamp}_{unique_id}_{file.filename}"
    filepath = f"{user_id}/{filename}"

    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filepath}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/octet-stream"
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(upload_url, content=content, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Upload failed: {response.text}")

    return {
        "success": True,
        "file_path": filepath,
        "file_name": file.filename,
        "file_size": len(content),
        "document_type": document_type
    }


@router.get("/api/background-check-documents/download/{file_path:path}")
async def download_document(
    file_path: str,
    user_id: str = Depends(get_authenticated_user_id)
):
    if not file_path.startswith(f"{user_id}/"):
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Access denied")

    download_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}"
    headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(download_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="File not found")

    return StreamingResponse(BytesIO(response.content), media_type="application/octet-stream")


@router.delete("/api/background-check-documents/delete/{file_path:path}")
async def delete_document(
    file_path: str,
    user_id: str = Depends(get_authenticated_user_id)
):
    if not file_path.startswith(f"{user_id}/"):
        raise HTTPException(status_code=403, detail="Access denied")

    delete_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}"
    headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}

    async with httpx.AsyncClient() as client:
        response = await client.delete(delete_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Delete failed")

    return {"success": True, "message": "File deleted successfully"}
