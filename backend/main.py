# backend/main.py
from fastapi import FastAPI
from routers import interview_requests
from config import settings
from routers import caregiver_profiles
from fastapi.middleware.cors import CORSMiddleware
from routers import session_routes  # adjust path as needed
from routers import care_requests
from routers import interview_requests  # Add your other routers here
from routers import care_applications
from routers import care_services
from routers import caregiver_references
from routers import caregiver_reviews
from routers import agencies
from routers import background_check_documents
from routers import care_disputes
from routers.care_request_status_history import router as care_status_history_router
from routers.daily_status_reports import router as daily_status_router
from routers import direct_messages
from routers import health_profiles
from routers import health_reports
from routers import medications
from routers import profiles
from routers import user_roles
from routers import dynamic_query
from routers import rule_query
from routers import simple_rule_engine
from routers import user_roles_util
from routers import file_storage
import uvicorn
from routers import sessiongoogle
from routers import background_verification_process
from routers import count_care_applications_by_status
from routers.enums import router as enums_router
from routers import agreementgeneration
from routers import agreements
from fastapi.staticfiles import StaticFiles
from routers import face_capture
from fastapi.staticfiles import StaticFiles
from routers import face_capture
from fastapi.responses import HTMLResponse
from routers.face_recognition import router as face_recognition_router
from routers.digital_signatures import router as digital_signatures_router
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


app = FastAPI(
    title="CareConnect Backend",
    description="APIs for Caregiver platform",
    version="1.0.0"
)

origins = ["*"]  # Customize this for production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: print to verify
print("SUPABASE_DB_URL =", settings.SUPABASE_DB_URL)
app.include_router(agreementgeneration.router, prefix="/api/agreementsgeneration", tags=["Agreements"])
app.include_router(agreements.router, prefix="/api/agreements", tags=["Agreements"])
app.include_router(session_routes.router, prefix="/api/session",tags=["session"])
app.include_router(session_routes.router,prefix="/api/session",tags=["session"])
app.include_router(sessiongoogle.router, tags=["Auth"])
app.include_router(
    agencies.router,
    prefix="/api",
    tags=["Agencies"]
)
app.include_router(enums_router, prefix="/api/v1/enums", tags=["ENUM Types"])
app.include_router(
    background_check_documents.router,
    prefix="/api",
    tags=["Background Check Documents"]
)

app.include_router(background_verification_process.router,
    prefix="/api",
    tags=["background_verification_process"])
app.include_router(caregiver_profiles.router)
# Registering the care_requests router with a custom prefix and tag
app.include_router(
    care_requests.router,
    prefix="/api/care_requests",
    tags=["Care Requests"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(digital_signatures_router, prefix="/api")
app.include_router(face_capture.router)
#app.include_router(face_recognition.router, prefix="/face", tags=["Face Recognition"])
app.include_router(face_recognition_router)
# Add other routers similarly
# app.include_router(caregiver_profiles.router, prefix="/api/caregivers", tags=["Caregiver Profiles"])
# app.include_router(care_requests.router, prefix="/api/care_requests", tags=["Care Requests"])

app.include_router(
    care_applications.router,
    prefix="/api",
    tags=["Care Applications"]
)
app.include_router(count_care_applications_by_status.care_app_status_router,
    prefix="/api",
    tags=["Care Applications"])
app.include_router(
    care_services.router,
    prefix="/api",
    tags=["Care Services"]
)
app.include_router(
    caregiver_references.router,
    prefix="/api",
    tags=["Caregiver References"]
)
app.include_router(
    caregiver_reviews.router,
    prefix="/api",
    tags=["Caregiver Reviews"]
)
app.include_router(
    care_disputes.router,
    prefix="/api",
    tags=["Care Disputes"]
)
app.include_router(
    care_status_history_router,
    prefix="/api",
    tags=["Care Request Status History"]
)
app.include_router(
    daily_status_router,
    prefix="/api",
    tags=["Daily Status Reports"]
)
app.include_router(
    direct_messages.router,
    prefix="/api/direct-messages",
    tags=["Direct Messages"]
)
app.include_router(file_storage.router,prefix="/api/background-documents",
    tags=["file storage"])
app.include_router(
    health_profiles.router,
    prefix="/api/health_profiles",
    tags=["Health Profiles"]
)
app.include_router(
    health_reports.router,
    prefix="/api/health_reports",
    tags=["Health Reports"]
)
app.include_router(interview_requests.router, prefix="/api/interviews", tags=["Interview Requests"])
# Register routers
app.include_router(
    interview_requests.router,
    prefix="/api/interviews",
    tags=["Interview Requests"]
)
app.include_router(
    medications.router,
    prefix="/api/medications",
    tags=["Medications"]
)
app.include_router(
    profiles.router,
    prefix="/api/profiles",
    tags=["Profiles"]
)

app.include_router(
    dynamic_query.router,
    prefix="/api/query",
    tags=["Dynamic Query"]
)
app.include_router(
    rule_query.router,
    prefix="/api/rules",
    tags=["Rule Engine"]
)
app.include_router(
    simple_rule_engine.router,
    prefix="/api",
    tags=["Simple Rule Engine"]
)
app.include_router(
    user_roles.router,
    prefix="/api/user_roles",
    tags=["User Roles"]
)
app.include_router(user_roles_util.router, tags=["User Roles Utility"])

# Serve the camera-based HTML at "/"
@app.get("/", response_class=HTMLResponse)
def serve_face_capture_ui():
    with open("static/capture.html", "r") as f:
        return f.read()