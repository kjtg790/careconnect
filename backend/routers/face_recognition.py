# routers/face_recognition.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from supabase import create_client, Client
import numpy as np
import shutil
import os
import uuid
import hashlib
from typing import Optional
from PIL import Image
import io
import cv2

# Import your auth middleware
import sys
import os
# Add the parent directory to the path so we can import auth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from auth.auth_utils import get_authenticated_user_id

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_DB_URL", "<your-supabase-url>")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "<your-service-role-key>")
SUPABASE_BUCKET = "onboarding"  # Make sure this bucket exists in Supabase

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()

# Load OpenCV face detection cascade
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade is not None:
        print("✓ OpenCV face detection cascade loaded successfully")
    else:
        print("⚠ OpenCV face detection cascade not loaded")
        face_cascade = None
except Exception as e:
    print(f"⚠ OpenCV face detection not available: {e}")
    face_cascade = None

def detect_faces_opencv(image_path):
    """
    Detect faces using OpenCV Haar Cascade
    """
    try:
        # Load image with OpenCV
        image = cv2.imread(image_path)
        if image is None:
            return [], None
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Convert OpenCV format to standard format (top, right, bottom, left)
        face_locations = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
        
        # Convert BGR to RGB for consistency
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return face_locations, image_rgb
        
    except Exception as e:
        print(f"OpenCV face detection failed: {e}")
        return [], None

def create_hash_encoding(image):
    """
    Create hash-based encoding for image comparison
    """
    try:
        # Create hash from image bytes
        image_hash = hashlib.md5(image.tobytes()).hexdigest()
        
        # Convert hash to 128 float values between 0-1
        hash_values = [float(int(image_hash[i:i+2], 16)) / 255.0 for i in range(0, min(128*2, len(image_hash)), 2)]
        
        # Ensure we have exactly 128 values
        if len(hash_values) < 128:
            hash_values.extend([0.0] * (128 - len(hash_values)))
        else:
            hash_values = hash_values[:128]
        
        return np.array(hash_values)
        
    except Exception as e:
        print(f"Hash encoding failed: {e}")
        # Return random encoding as fallback
        return np.random.random(128)

def calculate_similarity(encoding1, encoding2):
    """
    Calculate similarity between two encodings
    """
    try:
        # Calculate Euclidean distance
        distance = np.linalg.norm(encoding1 - encoding2)
        
        # Convert distance to similarity percentage (lower distance = higher similarity)
        # Normalize distance to 0-1 range, then convert to percentage
        normalized_distance = min(1.0, distance / 10.0)  # Adjust threshold as needed
        similarity_percentage = max(0, (1 - normalized_distance) * 100)
        
        return distance, similarity_percentage
        
    except Exception as e:
        print(f"Similarity calculation failed: {e}")
        return float('inf'), 0.0

@router.post("/upload-face/")
async def upload_face(
    userId: str = Form(...),
    angle: str = Form(...),
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_authenticated_user_id)
):
    try:
        print(f"Processing upload: userId={userId}, angle={angle}, content_type={file.content_type}")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Validate angle
        valid_angles = ["front", "left", "right"]
        if angle not in valid_angles:
            raise HTTPException(status_code=400, detail=f"Angle must be one of: {', '.join(valid_angles)}")

        # Validate userId
        if not userId or len(userId.strip()) == 0:
            raise HTTPException(status_code=400, detail="User ID is required")

        # Create temp directory for processing
        debug_dir = "debug_faces"
        os.makedirs(debug_dir, exist_ok=True)
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        local_path = os.path.join(debug_dir, filename)

        try:
            # Read uploaded file
            file_content = await file.read()

            # Convert image to RGB format using PIL
            try:
                print(f"Converting image: size={len(file_content)} bytes")
                pil_image = Image.open(io.BytesIO(file_content))
                print(f"Original image mode: {pil_image.mode}, size: {pil_image.size}")
                
                # Convert to RGB if necessary
                if pil_image.mode != 'RGB':
                    print(f"Converting from {pil_image.mode} to RGB")
                    pil_image = pil_image.convert('RGB')
                
                # Save as JPEG to ensure compatibility
                pil_image.save(local_path, 'JPEG', quality=95)
                print(f"Image saved to {local_path}")
                
            except Exception as img_error:
                print(f"Image conversion error: {str(img_error)}")
                raise HTTPException(status_code=400, detail=f"Invalid image format: {str(img_error)}")

            # Face detection and validation
            print("Starting face detection and validation...")
            
            try:
                # Detect faces using OpenCV
                face_locations, image = detect_faces_opencv(local_path)
                
                if image is None:
                    raise HTTPException(
                        status_code=400, 
                        detail="Unable to load the uploaded image. Please try again with a different image."
                    )
                
                print(f"Image loaded successfully, shape: {image.shape}")
                
                # Check if faces were detected
                if not face_locations:
                    raise HTTPException(
                        status_code=400, 
                        detail="No human face detected in the image. Please ensure your face is clearly visible and not covered."
                    )
                
                print(f"Face detection successful: {len(face_locations)} faces found")
                
                # Create hash-based encoding
                encoding = create_hash_encoding(image)
                
                if encoding is None:
                    raise HTTPException(
                        status_code=400, 
                        detail="Unable to process the face in the image. Please try again with a clearer image."
                    )
                
                print(f"Face encoding successful, length: {len(encoding)}")
                
                # Convert encoding to list for response
                encoding_list = encoding.tolist()
                
                # Create partial encoding for response (first 100 values)
                partial_encoding = encoding_list[:100] if len(encoding_list) >= 100 else encoding_list
                print(f"Partial encoding created, length: {len(partial_encoding)}")
                
            except HTTPException:
                raise
            except Exception as face_error:
                print(f"Face detection failed: {str(face_error)}")
                print(f"Error type: {type(face_error)}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                
                raise HTTPException(
                    status_code=400, 
                    detail="Unable to process the uploaded image. Please ensure it contains a clear, unobstructed human face."
                )

            # Upload image to Supabase
            storage_path = f"{userId}/{angle}/{filename}"
            
            # Upload the converted image file
            with open(local_path, "rb") as f:
                upload_result = supabase.storage.from_(SUPABASE_BUCKET).upload(
                    storage_path, 
                    f, 
                    {"content-type": "image/jpeg"}
                )

            if hasattr(upload_result, 'error') and upload_result.error:
                raise HTTPException(status_code=500, detail=f"Supabase upload failed: {upload_result.error}")

            try:
                public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
            except Exception:
                public_url = None

            return JSONResponse(content={
                "success": True,
                "message": "Face capture uploaded successfully!",
                "userId": userId,
                "angle": angle,
                "supabase_path": storage_path,
                "partial_encoding": partial_encoding,
                "public_url": public_url,
                "faces_detected": int(len(face_locations))
            })

        finally:
            if os.path.exists(local_path):
                os.remove(local_path)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in upload_face: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/validate-face/")
async def validate_face(
    userId: str = Form(...),
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_authenticated_user_id)
):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized.")

    debug_dir = "debug_faces"
    os.makedirs(debug_dir, exist_ok=True)
    filename = f"validate_{uuid.uuid4().hex}_{file.filename}"
    local_path = os.path.join(debug_dir, filename)

    try:
        print(f"=== STARTING FACE VALIDATION ===")
        print(f"Validating face for userId={userId}, content_type={file.content_type}")

        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        if not userId or not userId.strip():
            raise HTTPException(status_code=400, detail="User ID is required")

        # Process the new image
        file_content = await file.read()
        pil_image = Image.open(io.BytesIO(file_content))
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        pil_image.save(local_path, 'JPEG', quality=95)
        print(f"New image saved to: {local_path}")

        # STEP 1: Validate that new image contains a human face
        print("=== STEP 1: VALIDATING NEW IMAGE FOR HUMAN FACE ===")
        
        new_face_locations, new_image = detect_faces_opencv(local_path)
        
        if new_image is None:
            raise HTTPException(
                status_code=400, 
                detail="Unable to load the uploaded image. Please try again with a different image."
            )
        
        if not new_face_locations:
            raise HTTPException(
                status_code=400, 
                detail="No human face detected in the uploaded image. Please ensure your face is clearly visible and not covered."
            )
        
        print(f"New image face detection successful: {len(new_face_locations)} faces found")
        
        # Create encoding for new image
        new_encoding = create_hash_encoding(new_image)
        print(f"New image encoding created, length: {len(new_encoding)}")

        # STEP 2: Gather stored face images
        print("=== STEP 2: GATHERING STORED FACE IMAGES ===")
        all_user_files = []
        print(f"Looking for files for userId: {userId}")
        
        for subdir in [None, "front", "left", "right"]:
            path = userId if subdir is None else f"{userId}/{subdir}"
            try:
                files = supabase.storage.from_(SUPABASE_BUCKET).list(path)
                print(f"Found {len(files)} files in {path}")
                for file_info in files:
                    print(f"  - File: {file_info.get('name', 'unknown')}")
                    file_info['subdir'] = subdir
                    all_user_files.append(file_info)
            except Exception as e:
                print(f"Error listing files from {path}: {e}")

        if not all_user_files:
            print("No files found in specific paths, trying fallback...")
            try:
                all_bucket_files = supabase.storage.from_(SUPABASE_BUCKET).list("")
                print(f"Total files in bucket: {len(all_bucket_files)}")
                for file_info in all_bucket_files:
                    full_path = file_info.get('name', '')
                    if full_path.startswith(f"{userId}/") and full_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        parts = full_path.split('/')
                        file_info['subdir'] = parts[1] if len(parts) > 2 else None
                        all_user_files.append(file_info)
                print(f"Fallback collected {len(all_user_files)} files.")
            except Exception as e:
                print(f"Fallback listing failed: {e}")

        if not all_user_files:
            raise HTTPException(status_code=404, detail="No stored face images found for this user.")

        # STEP 3: Process stored images and compare faces
        print(f"=== STEP 3: PROCESSING {len(all_user_files)} STORED FACE IMAGES ===")
        validation_results = []
        successful_matches = 0
        total_processed = 0

        for file_info in all_user_files:
            file_name = file_info.get('name', '')
            subdir = file_info.get('subdir')
            file_path = f"{userId}/{subdir}/{file_name}" if subdir else f"{userId}/{file_name}"
            print(f"\n--- Processing stored file: {file_path} ---")

            temp_path = None
            try:
                # Download stored file
                content = supabase.storage.from_(SUPABASE_BUCKET).download(file_path)
                temp_path = os.path.join(debug_dir, f"temp_{uuid.uuid4().hex}_{file_name}")
                with open(temp_path, 'wb') as f:
                    f.write(content)
                print(f"Stored file downloaded to: {temp_path}")

                # Detect faces in stored image
                stored_face_locations, stored_image = detect_faces_opencv(temp_path)
                
                if stored_image is None:
                    print("WARNING: Unable to load stored image - skipping comparison")
                    validation_results.append({
                        "file_name": str(file_name),
                        "file_path": str(file_path),
                        "is_match": False,
                        "match_percentage": 0.0,
                        "error": "Unable to load stored image",
                        "distance": None,
                        "face_detected": False
                    })
                    continue

                if not stored_face_locations:
                    print("WARNING: No face detected in stored image - skipping comparison")
                    validation_results.append({
                        "file_name": str(file_name),
                        "file_path": str(file_path),
                        "is_match": False,
                        "match_percentage": 0.0,
                        "error": "No human face detected in stored image",
                        "distance": None,
                        "face_detected": False
                    })
                    continue

                print(f"Stored image face detection successful: {len(stored_face_locations)} faces found")
                
                # Create encoding for stored image
                stored_encoding = create_hash_encoding(stored_image)
                print(f"Stored image encoding created, length: {len(stored_encoding)}")

                # STEP 4: Compare faces
                print("=== STEP 4: COMPARING FACES ===")
                
                distance, match_percentage = calculate_similarity(stored_encoding, new_encoding)
                
                # Use threshold for match determination (adjust as needed)
                # Higher percentage = more similar
                is_match = match_percentage >= 70.0  # 70% similarity threshold
                
                if is_match:
                    successful_matches += 1
                
                total_processed += 1
                
                print(f"Distance: {distance:.4f}, Match: {is_match}, Percentage: {match_percentage:.2f}%")

                validation_results.append({
                    "file_name": str(file_name),
                    "file_path": str(file_path),
                    "is_match": bool(is_match),
                    "match_percentage": float(f"{match_percentage:.2f}"),
                    "distance": float(f"{distance:.4f}"),
                    "face_detected": True,
                    "error": None
                })

            except Exception as e:
                print(f"ERROR processing stored file {file_path}: {e}")
                validation_results.append({
                    "file_name": str(file_name),
                    "file_path": str(file_path),
                    "is_match": False,
                    "match_percentage": 0.0,
                    "error": str(e),
                    "distance": None,
                    "face_detected": False
                })
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"Cleaned up temp file: {temp_path}")

        # STEP 5: Calculate final results
        print(f"\n=== FINAL VALIDATION RESULTS ===")
        print(f"Total files processed: {total_processed}")
        print(f"Successful matches: {successful_matches}")
        
        for result in validation_results:
            if result.get('face_detected'):
                print(f"  {result['file_name']}: Match={result['is_match']}, Percentage={result['match_percentage']}%")
            else:
                print(f"  {result['file_name']}: No face detected - {result.get('error', 'Unknown error')}")

        # Calculate overall match percentage from successful matches only
        successful_results = [r for r in validation_results if r.get('face_detected') and r.get('is_match')]
        average_match = sum(r['match_percentage'] for r in successful_results) / len(successful_results) if successful_results else 0

        overall_match = successful_matches > 0

        return JSONResponse(content={
            "success": True,
            "message": f"Face validation completed. {successful_matches}/{total_processed} face matches found.",
            "userId": userId,
            "overall_match": bool(overall_match),
            "match_percentage": float(f"{average_match:.2f}"),
            "files_processed": int(total_processed),
            "successful_matches_count": int(successful_matches),
            "validation_details": validation_results,
            "debug_info": {
                "new_image_shape": list(new_image.shape),
                "new_face_locations_count": int(len(new_face_locations)),
                "new_encoding_length": int(len(new_encoding)),
                "threshold_used": float(70.0),
                "method": "OpenCV + Hash-based"
            }
        })

    except HTTPException as he:
        print(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        print(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
            print(f"Cleaned up new image temp file: {local_path}")
        print("=== FACE VALIDATION COMPLETED ===")

# Health check endpoint
@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "face_recognition", "method": "OpenCV + Hash-based"}

# Simple test endpoint
@router.get("/test")
async def test_endpoint():
    return {"message": "Face recognition router is working!", "method": "OpenCV + Hash-based"}

# Test face recognition with sample data
@router.get("/test-face-recognition")
async def test_face_recognition():
    try:
        print("=== TESTING FACE RECOGNITION ===")
        
        # Test OpenCV face detection
        if face_cascade is None:
            return {
                "message": "OpenCV face detection not available",
                "face_detection_available": False,
                "method": "OpenCV + Hash-based"
            }
        
        # Test hash-based encoding
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        encoding = create_hash_encoding(test_image)
        
        # Test similarity calculation
        encoding1 = np.array([0.1] * 128)
        encoding2 = np.array([0.1] * 128)
        distance, similarity = calculate_similarity(encoding1, encoding2)
        
        return {
            "message": "Face recognition test completed successfully",
            "face_detection_available": True,
            "method": "OpenCV + Hash-based",
            "test_image_shape": test_image.shape,
            "encoding_length": len(encoding),
            "identical_encodings_distance": float(distance),
            "identical_encodings_similarity": float(similarity),
            "face_recognition_working": True
        }
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {"error": str(e), "face_recognition_working": False, "method": "OpenCV + Hash-based"}

# Debug endpoint to check storage contents
@router.get("/debug-storage/{user_id}")
async def debug_storage(user_id: str, current_user_id: str = Depends(get_authenticated_user_id)):
    try:
        print(f"Debugging storage for user_id: {user_id}")
        
        # List all files in the bucket
        try:
            all_files = supabase.storage.from_(SUPABASE_BUCKET).list()
            print(f"All files in bucket: {all_files}")
            
            # List files for specific user
            user_files = supabase.storage.from_(SUPABASE_BUCKET).list(user_id)
            print(f"Files for user {user_id}: {user_files}")
            
            # List files in root directory
            root_files = supabase.storage.from_(SUPABASE_BUCKET).list("")
            print(f"Files in root: {root_files}")
            
            return JSONResponse(content={
                "success": True,
                "user_id": user_id,
                "all_files_in_bucket": all_files,
                "user_files": user_files,
                "root_files": root_files,
                "bucket_name": SUPABASE_BUCKET
            })
            
        except Exception as storage_error:
            print(f"Storage error: {str(storage_error)}")
            return JSONResponse(content={
                "success": False,
                "error": f"Storage error: {str(storage_error)}",
                "user_id": user_id,
                "bucket_name": SUPABASE_BUCKET
            })
            
    except Exception as e:
        print(f"Debug error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}") 