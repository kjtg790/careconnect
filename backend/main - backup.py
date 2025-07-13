from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import ALLOWED_ORIGINS
from fastapi.responses import JSONResponse
import traceback
# Import routers
from care_requests import router as care_requests_router
from care_applications import router as care_applications_router
from caregiver_profiles import router as caregiver_profiles_router
from interviews import router as interviews_router
from direct_messages import router as direct_messages_router
from references import router as references_router
from disputes import router as disputes_router
from agency import router as agency_router
from profiles import router as profiles_router
from routes.update_interview import router as update_interview_router 
from jwt_auth_demo import router as auth_router

# Create FastAPI app
app = FastAPI(
    title="Home Harmony Care API",
    version="1.0.0",
    description="API for Home Harmony Care application"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )

# ✅ Debug: Show that routers are being loaded
print("✅ Including update_interview_router")

# Include routers
app.include_router(auth_router)
app.include_router(care_requests_router)
app.include_router(care_applications_router)
app.include_router(caregiver_profiles_router)
app.include_router(interviews_router)
app.include_router(direct_messages_router)
app.include_router(references_router)
app.include_router(disputes_router)
app.include_router(agency_router)
app.include_router(profiles_router)


app.include_router(update_interview_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Home Harmony Care API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True
    )