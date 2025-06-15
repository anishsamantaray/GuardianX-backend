from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
JWT_ALGORITHM=os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES=int(os.getenv('JWT_EXPIRE_MINUTES', 60))
JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY')
JWT_REFRESH_EXPIRE_MINUTES=int(os.getenv('JWT_REFRESH_EXPIRE_MINUTES', 1440))  # Default to 24 hours

def create_access_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = { "sub": email, "exp": expire }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload["sub"]  # email
    except JWTError:
        return None

def create_refresh_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=JWT_REFRESH_EXPIRE_MINUTES)
    return jwt.encode({ "sub": email, "exp": expire }, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)