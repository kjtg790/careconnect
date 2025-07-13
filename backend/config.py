# backend/config.py
from pydantic import BaseSettings
from dotenv import load_dotenv
import os

# Load .env explicitly
load_dotenv()

class Settings(BaseSettings):
    SUPABASE_DB_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_DB: str
    class Config:
        env_file = ".env"

settings = Settings()
