from pydantic import BaseModel
from typing import List, Optional

class ApplyRequest(BaseModel):
    care_request_id: str
    user_id: str

    class Config:
        schema_extra = {
            "example": {
                "care_request_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }

class CaregiverProfile(BaseModel):
    user_id: str
    full_name: str
    care_services: List[str]
    experience_description: Optional[str] = None
    qualifications: Optional[str] = None
    availability: Optional[str] = None
    hourly_rate: Optional[float] = None
    avatar_url: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "full_name": "Jane Doe",
                "care_services": ["elderly_care", "companionship"],
                "experience_description": "5 years of experience",
                "hourly_rate": 25.0
            }
        }

class InterviewRequest(BaseModel):
    requester_id: str
    caregiver_user_id: str
    care_request_id: Optional[str] = None
    care_application_id: Optional[str] = None
    scheduled_date_time: str
    message: Optional[str] = None
    status: str = "scheduled"

    class Config:
        schema_extra = {
            "example": {
                "requester_id": "123e4567-e89b-12d3-a456-426614174000",
                "caregiver_user_id": "123e4567-e89b-12d3-a456-426614174001",
                "scheduled_date_time": "2024-01-15T14:00:00Z",
                "message": "Please join us for an interview"
            }
        }

class InterviewUpdate(BaseModel):
    interview_id: str
    status: Optional[str] = None
    scheduled_date_time: Optional[str] = None
    message: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "interview_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "accepted",
                "scheduled_date_time": "2024-01-15T14:00:00Z"
            }
        }