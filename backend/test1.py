import jwt
import datetime

# Use your actual secret
SUPABASE_JWT_SECRET = "hZthWsGyjZI/emXKOyYJutn3AyDa2mrwZ7EpwNu1MWQMEkIJCrJAVT/6M25PBEPliuDiCxrnDXtW+JC8sfSv/g=="

# Simulate a real Supabase user ID (UUID format)
user_id = "7b995c08-9c0c-4097-9e87-e8948a94f7d6"  # Replace with actual requester_id or caregiver_user_id

# Set payload
payload = {
    "sub": user_id,
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}

# Encode JWT
token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")

print("🔐 Authorization Header:")
print(f"Bearer {token}")
