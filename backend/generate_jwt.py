import jwt
import time
from auth.auth_utils import get_authenticated_user_id

# Supabase JWT secret (from Project Settings > API)
SUPABASE_JWT_SECRET = "your_supabase_jwt_secret"

# Example user ID from Supabase auth.users table
user_id = "7b995c08-9c0c-4097-9e87-e8948a94f7d6"

# Expiration (1 hour from now)
exp = int(time.time()) + 3600  # 1 hour

# JWT payload (required: sub, exp)
payload = {
    "sub": user_id,
    "exp": exp,
    # Optional: Add "role": "authenticated" or "service_role"
    "role": "authenticated"
}

# Encode token
token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithms=["RS256"])

print("✅ Generated Supabase JWT:\n")
print(f"Bearer {token}")
