import os
import io
import logging
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from PIL import Image, UnidentifiedImageError
import face_recognition
from supabase import create_client, Client
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv
router = APIRouter()
# Load env variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "onboarding")

# Setup Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()
logger = logging.getLogger("face_recognition")
logging.basicConfig(level=logging.DEBUG)

@router.post("/save-face-encodings")
async def save_face_encodings(user_id: str = Form(...), file: UploadFile = File(...)):
    logger.info(f"Received request to save face encodings for user: {user_id}")
    
    try:
        logger.info(f"Processing file: {file.filename}, content type: {file.content_type}")
        contents = await file.read()
        logger.debug(f"Raw file size: {len(contents)} bytes")
        
        # Upload image to Supabase Storage
        filename = f"{user_id}_{datetime.utcnow().isoformat()}_{uuid4().hex}.jpg"
        path_on_bucket = f"{user_id}/{filename}"
        logger.info(f"Uploading image to Supabase bucket path: {path_on_bucket}")
        
        try:
            upload_response = supabase.storage.from_(SUPABASE_BUCKET).upload(path_on_bucket, contents, {"content-type": file.content_type})
            logger.debug(f"Upload response: {upload_response}")
        except Exception as e:
            logger.exception("Supabase upload failed.")
            raise HTTPException(status_code=500, detail="Failed to upload image to Supabase storage.")

        # Process face recognition
        image_stream = io.BytesIO(contents)
        try:
            img = Image.open(image_stream)
        except UnidentifiedImageError:
            logger.exception("PIL could not identify the image file.")
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

        logger.debug(f"Original image mode: {img.mode}, format: {img.format}")
        
        if img.mode not in ['RGB', 'L']:
            img = img.convert('RGB')
            logger.debug("Converted image mode to RGB")

        np_image = np.array(img)
        logger.debug(f"Numpy image shape: {np_image.shape}, dtype: {np_image.dtype}")

        if np_image.dtype != np.uint8:
            logger.error("Image is not 8-bit format.")
            raise HTTPException(status_code=400, detail="Image is not 8-bit format.")
        
        if len(np_image.shape) != 3 or np_image.shape[2] != 3:
            logger.error("Image is not RGB with 3 channels.")
            raise HTTPException(status_code=400, detail="Image must be RGB with 3 channels.")

        try:
            face_locations = face_recognition.face_locations(np_image)
            logger.debug(f"Face locations found: {face_locations}")
        except Exception as e:
            logger.exception("Face detection failed.")
            raise HTTPException(status_code=400, detail=f"Face detection error: {str(e)}")

        if not face_locations:
            logger.warning("No face detected.")
            raise HTTPException(status_code=404, detail="No face detected in image.")

        face_encodings = face_recognition.face_encodings(np_image, face_locations)
        logger.debug(f"Face encodings count: {len(face_encodings)}")

        if not face_encodings:
            logger.warning("Face found but encoding failed.")
            raise HTTPException(status_code=404, detail="Failed to encode face.")

        encoding = face_encodings[0].tolist()
        logger.info(f"Encoding successful for user {user_id}")

        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path_on_bucket)
        return {
            "user_id": user_id,
            "encoding": encoding,
            "image_path": path_on_bucket,
            "image_url": public_url
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Unexpected error occurred.")
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
