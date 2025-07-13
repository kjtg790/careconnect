import jwt
import datetime

JWT_SECRET = "your-secret"
payload = {
    "sub": "user-id-123",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)  # expires in 7 days
}

token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
