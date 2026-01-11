from fastapi import Header, HTTPException
from app.utils.auth import verify_token


def get_current_user(
    authorization: str = Header(...)
) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.split(" ")[1]
    email = verify_token(token)

    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return email.lower()
