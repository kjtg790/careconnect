from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import os
import uuid
from datetime import datetime

router = APIRouter()

SAVE_DIR = "captured_faces"
os.makedirs(SAVE_DIR, exist_ok=True)

@router.get("/face-capture", response_class=HTMLResponse)
async def get_face_capture_page():
    with open("static/capture.html", "r") as file:
        return file.read()

@router.post("/upload-face")
async def upload_face(file: UploadFile = File(...), angle: str = Form(...)):
    filename = f"{angle}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "success", "filename": filename}
