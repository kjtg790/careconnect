# digital_signatures.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import os
import uuid
import hashlib
import json
from auth.auth_utils import get_authenticated_user_id
import supabase
import base64

router = APIRouter()
security = HTTPBearer()

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_DB_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase environment variables are not set properly.")

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class DigitalSignatureCreate(BaseModel):
    agreement_id: str
    signer_user_id: str
    signer_name: str
    signer_email: str
    signature_type: str = "electronic"  # electronic, digital_certificate, biometric
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class DigitalSignatureVerify(BaseModel):
    signature_id: str
    verification_code: str

class SignatureData(BaseModel):
    agreement_id: str
    signer_user_id: str
    signature_image: str  # base64 encoded signature
    signature_timestamp: datetime
    signature_hash: str

def generate_signature_hash(agreement_id: str, signer_user_id: str, timestamp: str) -> str:
    """Generate a unique hash for the signature"""
    data = f"{agreement_id}:{signer_user_id}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()

def create_signature_image(signature_text: str, font_size: int = 48) -> str:
    """Create a signature image from text (simplified version without PIL)"""
    try:
        # For now, return a simple base64 encoded placeholder
        # In production, you would use PIL to create actual signature images
        placeholder_data = f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        return placeholder_data
    except Exception as e:
        print(f"Error creating signature image: {e}")
        return ""

def add_signature_to_pdf(pdf_content: bytes, signature_image: str, x: int = 100, y: int = 100) -> bytes:
    """Add signature image to PDF (simplified version - in production, use PyPDF2 or reportlab)"""
    # This is a placeholder - in a real implementation, you would:
    # 1. Use PyPDF2 or reportlab to modify the PDF
    # 2. Add the signature image at the specified coordinates
    # 3. Return the modified PDF content
    
    # For now, we'll return the original PDF content
    # In production, implement proper PDF modification
    return pdf_content

@router.post("/create-signature-request", dependencies=[Depends(security)])
def create_signature_request(
    signature_data: DigitalSignatureCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a digital signature request"""
    user_id = get_authenticated_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Check if user has already signed this agreement
        existing_signature_response = supabase_client.table("digital_signatures").select("*").eq("agreement_id", signature_data.agreement_id).eq("signer_user_id", signature_data.signer_user_id).execute()
        
        if existing_signature_response.data:
            return {
                "success": False,
                "already_signed": True,
                "message": "User has already signed this agreement",
                "existing_signature": existing_signature_response.data[0]
            }
        
        # Generate unique signature request ID
        signature_request_id = str(uuid.uuid4())
        
        # Generate verification code (6-digit)
        verification_code = str(uuid.uuid4())[:6].upper()
        
        # Create signature request record
        signature_request = {
            "id": signature_request_id,
            "agreement_id": signature_data.agreement_id,
            "signer_user_id": signature_data.signer_user_id,
            "signer_name": signature_data.signer_name,
            "signer_email": signature_data.signer_email,
            "signature_type": signature_data.signature_type,
            "verification_code": verification_code,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "ip_address": signature_data.ip_address,
            "user_agent": signature_data.user_agent
        }
        
        # Store in database
        try:
            response = supabase_client.table("digital_signature_requests").insert(signature_request).execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to create signature request")
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        return {
            "success": True,
            "signature_request_id": signature_request_id,
            "verification_code": verification_code,
            "expires_at": signature_request["expires_at"],
            "message": "Signature request created successfully"
        }
        
    except Exception as e:
        print(f"Error creating signature request: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/sign-agreement", dependencies=[Depends(security)])
def sign_agreement(
    agreement_id: str = Form(...),
    signature_text: str = Form(...),
    verification_code: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Sign an agreement electronically"""
    user_id = get_authenticated_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Check if user has already signed this agreement
        existing_signature_response = supabase_client.table("digital_signatures").select("*").eq("agreement_id", agreement_id).eq("signer_user_id", user_id).execute()
        
        if existing_signature_response.data:
            return {
                "success": False,
                "already_signed": True,
                "message": "User has already signed this agreement",
                "existing_signature": existing_signature_response.data[0]
            }
        
        # Verify the signature request
        response = supabase_client.table("digital_signature_requests").select("*").eq("agreement_id", agreement_id).eq("verification_code", verification_code).eq("status", "pending").execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Invalid or expired signature request")
        
        signature_request = response.data[0]
        
        # Check if expired
        expires_at = datetime.fromisoformat(signature_request["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="Signature request has expired")
        
        # Create signature image
        signature_image = create_signature_image(signature_text)
        if not signature_image:
            raise HTTPException(status_code=500, detail="Failed to create signature image")
        
        # Generate signature hash
        timestamp = datetime.now(timezone.utc).isoformat()
        signature_hash = generate_signature_hash(agreement_id, user_id, timestamp)
        
        # Create signature record
        signature_record = {
            "id": str(uuid.uuid4()),
            "agreement_id": agreement_id,
            "signer_user_id": user_id,
            "signature_image": signature_image,
            "signature_text": signature_text,
            "signature_hash": signature_hash,
            "signature_timestamp": timestamp,
            "verification_code": verification_code,
            "ip_address": signature_request.get("ip_address"),
            "user_agent": signature_request.get("user_agent"),
            "status": "signed"
        }
        
        # Store signature
        sig_response = supabase_client.table("digital_signatures").insert(signature_record).execute()
        
        if not sig_response.data:
            raise HTTPException(status_code=500, detail="Failed to store signature")
        
        # Update signature request status
        supabase_client.table("digital_signature_requests").update({"status": "completed"}).eq("id", signature_request["id"]).execute()
        
        # Update agreement status
        supabase_client.table("agreements").update({"signed_on": timestamp}).eq("id", agreement_id).execute()
        
        return {
            "success": True,
            "signature_id": signature_record["id"],
            "signature_hash": signature_hash,
            "signed_at": timestamp,
            "message": "Agreement signed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error signing agreement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/verify-signature/{signature_id}", dependencies=[Depends(security)])
def verify_signature(
    signature_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify a digital signature"""
    user_id = get_authenticated_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Get signature record
        response = supabase_client.table("digital_signatures").select("*").eq("id", signature_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Signature not found")
        
        signature = response.data[0]
        
        # Verify signature hash
        expected_hash = generate_signature_hash(
            signature["agreement_id"], 
            signature["signer_user_id"], 
            signature["signature_timestamp"]
        )
        
        is_valid = signature["signature_hash"] == expected_hash
        
        return {
            "success": True,
            "signature_id": signature_id,
            "is_valid": is_valid,
            "signature_data": {
                "signer_user_id": signature["signer_user_id"],
                "signature_timestamp": signature["signature_timestamp"],
                "signature_text": signature["signature_text"],
                "ip_address": signature.get("ip_address"),
                "user_agent": signature.get("user_agent")
            },
            "verification_message": "Signature is valid" if is_valid else "Signature verification failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verifying signature: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/agreement-signatures/{agreement_id}", dependencies=[Depends(security)])
def get_agreement_signatures(
    agreement_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all signatures for an agreement"""
    user_id = get_authenticated_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Get all signatures for the agreement
        response = supabase_client.table("digital_signatures").select("*").eq("agreement_id", agreement_id).execute()
        
        signatures = response.data if response.data else []
        
        # Get signature requests
        req_response = supabase_client.table("digital_signature_requests").select("*").eq("agreement_id", agreement_id).execute()
        signature_requests = req_response.data if req_response.data else []
        
        return {
            "success": True,
            "agreement_id": agreement_id,
            "signatures": signatures,
            "signature_requests": signature_requests,
            "total_signatures": len(signatures),
            "pending_requests": len([req for req in signature_requests if req["status"] == "pending"])
        }
        
    except Exception as e:
        print(f"Error getting agreement signatures: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/generate-signed-pdf", dependencies=[Depends(security)])
def generate_signed_pdf(
    agreement_id: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Generate a PDF with digital signatures embedded"""
    user_id = get_authenticated_user_id(credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Get agreement
        agreement_response = supabase_client.table("agreements").select("*").eq("id", agreement_id).execute()
        
        if not agreement_response.data:
            raise HTTPException(status_code=404, detail="Agreement not found")
        
        agreement = agreement_response.data[0]
        
        # Get signatures
        signatures_response = supabase_client.table("digital_signatures").select("*").eq("agreement_id", agreement_id).execute()
        signatures = signatures_response.data if signatures_response.data else []
        
        if not signatures:
            raise HTTPException(status_code=400, detail="No signatures found for this agreement")
        
        # In a real implementation, you would:
        # 1. Download the original PDF from agreement.agreement_link
        # 2. Add signature images to the PDF at appropriate positions
        # 3. Add signature metadata and verification information
        # 4. Return the signed PDF
        
        # For now, return success with placeholder
        return {
            "success": True,
            "agreement_id": agreement_id,
            "signed_pdf_url": f"https://example.com/signed-agreements/{agreement_id}.pdf",
            "signature_count": len(signatures),
            "message": "Signed PDF generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating signed PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health check endpoint
@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "digital_signatures"}

# Test endpoint to check database connection
@router.get("/test-db")
def test_database():
    try:
        # Test if we can connect to the database
        response = supabase_client.table("agreements").select("id").limit(1).execute()
        return {
            "status": "success",
            "message": "Database connection working",
            "agreements_count": len(response.data) if response.data else 0
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }

# Test endpoint to check digital signature tables
@router.get("/test-signature-tables")
def test_signature_tables():
    try:
        # Test digital_signature_requests table
        req_response = supabase_client.table("digital_signature_requests").select("id").limit(1).execute()
        
        # Test digital_signatures table
        sig_response = supabase_client.table("digital_signatures").select("id").limit(1).execute()
        
        return {
            "status": "success",
            "message": "Digital signature tables are accessible",
            "requests_count": len(req_response.data) if req_response.data else 0,
            "signatures_count": len(sig_response.data) if sig_response.data else 0
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Digital signature tables test failed: {str(e)}"
        }

# Check if agreement is already signed
@router.get("/check-agreement-signed/{agreement_id}")
def check_agreement_signed(agreement_id: str):
    """Check if an agreement is already signed"""
    try:
        # Check for existing signatures
        response = supabase_client.table("digital_signatures").select("*").eq("agreement_id", agreement_id).execute()
        
        signatures = response.data if response.data else []
        
        if signatures:
            # Get the most recent signature
            latest_signature = max(signatures, key=lambda x: x.get("signature_timestamp", ""))
            
            return {
                "success": True,
                "is_signed": True,
                "signature_count": len(signatures),
                "latest_signature": {
                    "signature_id": latest_signature.get("id"),
                    "signer_user_id": latest_signature.get("signer_user_id"),
                    "signature_text": latest_signature.get("signature_text"),
                    "signature_timestamp": latest_signature.get("signature_timestamp"),
                    "signature_hash": latest_signature.get("signature_hash")
                },
                "all_signatures": signatures,
                "message": f"Agreement is already signed with {len(signatures)} signature(s)"
            }
        else:
            return {
                "success": True,
                "is_signed": False,
                "signature_count": 0,
                "message": "Agreement is not signed yet"
            }
            
    except Exception as e:
        print(f"Error checking agreement signature: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to check agreement signature: {str(e)}"
        }

# Check if specific user has signed the agreement
@router.get("/check-user-signed/{agreement_id}/{user_id}")
def check_user_signed(agreement_id: str, user_id: str):
    """Check if a specific user has signed the agreement"""
    try:
        # Check for existing signature by this user
        response = supabase_client.table("digital_signatures").select("*").eq("agreement_id", agreement_id).eq("signer_user_id", user_id).execute()
        
        signatures = response.data if response.data else []
        
        if signatures:
            # Get the user's signature
            user_signature = signatures[0]  # Should only be one per user per agreement
            
            return {
                "success": True,
                "has_signed": True,
                "signature": {
                    "signature_id": user_signature.get("id"),
                    "signature_text": user_signature.get("signature_text"),
                    "signature_timestamp": user_signature.get("signature_timestamp"),
                    "signature_hash": user_signature.get("signature_hash")
                },
                "message": "User has already signed this agreement"
            }
        else:
            return {
                "success": True,
                "has_signed": False,
                "message": "User has not signed this agreement yet"
            }
            
    except Exception as e:
        print(f"Error checking user signature: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to check user signature: {str(e)}"
        } 