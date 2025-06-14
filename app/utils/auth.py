from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
JWT_ALGORITHM=os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES=int(os.getenv('JWT_EXPIRE_MINUTES', 60))
JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY')


def create_jwt_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = { "sub": email, "exp": expire }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload["sub"]  # email
    except JWTError:
        return None