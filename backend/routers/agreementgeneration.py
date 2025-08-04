from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from auth.auth_utils import get_authenticated_user_id
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import os
import requests
import pdfkit
import tempfile
import uuid
from jinja2 import Template, StrictUndefined, exceptions as jinja_exceptions

router = APIRouter()
security = HTTPBearer()

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_DB_URL", "").rstrip("/")  # Avoid trailing slash issues
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_BUCKET", "agreements")

# Configure wkhtmltopdf
WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
if not os.path.exists(WKHTMLTOPDF_PATH):
    raise RuntimeError(f"wkhtmltopdf not found at path: {WKHTMLTOPDF_PATH}")
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

class AgreementGenerationRequest(BaseModel):
    agreement_id: str
    agreement_type: str
    version: str
    placeholders: Dict[str, Any]

@router.post("/generate-pdf", tags=["Agreements"])
def generate_agreement_pdf_from_local_template(
    payload: AgreementGenerationRequest,
    user_id: str = Depends(get_authenticated_user_id)
):
    try:
        # Step 1: Load template file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_file = os.path.join(current_dir, "caregiver_agreement_template.html")

        if not os.path.isfile(template_file):
            raise HTTPException(status_code=500, detail=f"Template file not found at {template_file}")

        with open(template_file, "r", encoding="utf-8") as file:
            raw_template = file.read()

        if not raw_template.strip():
            raise HTTPException(status_code=400, detail="Template is empty.")

        # Step 2: Render HTML
        try:
            template = Template(raw_template, undefined=StrictUndefined)
            rendered_html = template.render(**payload.placeholders)
        except jinja_exceptions.UndefinedError as e:
            raise HTTPException(status_code=400, detail=f"Missing placeholder: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Template rendering failed: {str(e)}")

        # Step 3: Generate PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdfkit.from_string(rendered_html, tmp_pdf.name, configuration=PDFKIT_CONFIG)
            pdf_path = tmp_pdf.name

        # Step 4: Upload to Supabase Storage
        filename = f"agreement_{payload.agreement_id}_{uuid.uuid4().hex[:8]}.pdf"
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_STORAGE_BUCKET}/{filename}"

        with open(pdf_path, "rb") as f:
            file_data = f.read()

        upload_resp = requests.post(
            upload_url,
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": "application/pdf",
                "x-upsert": "true"
            },
            data=file_data
        )

        if upload_resp.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Upload failed: {upload_resp.status_code}, {upload_resp.text}")

        # Step 5: Public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{filename}"

        # Step 6: Update agreement record
        update_url = f"{SUPABASE_URL}/rest/v1/agreements?id=eq.{payload.agreement_id}"
        patch_resp = requests.patch(
            update_url,
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": "application/json"
            },
            json={"agreement_link": public_url}
        )

        if patch_resp.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail=f"Failed to update agreement record: {patch_resp.text}")

        return {
            "message": "Agreement PDF generated, uploaded, and linked successfully.",
            "agreement_link": public_url
        }

    except HTTPException:
        raise  # re-raise known exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")