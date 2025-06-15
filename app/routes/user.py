from fastapi import APIRouter, HTTPException, Query
from app.schemas.user_schemas import UserSignupRequest, OTPVerifyRequest, EmailRequest, RefreshTokenRequest
from app.utils.auth import  create_access_token, create_refresh_token, verify_token
from app.utils.db import check_user_by_email, create_user_document, generate_and_store_email_otp, verify_email_otp
from app.utils.email import send_otp_email

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/send-otp")
async def send_otp(payload: EmailRequest):
    exists = await check_user_by_email(payload.email)

    if exists:
        otp = await generate_and_store_email_otp(payload.email)
        await send_otp_email(payload.email, otp)
        return { "exists": True, "otp_sent": True }

    return { "exists": False }


@router.post("/verify-otp")
async def verify_otp(payload: OTPVerifyRequest):
    is_valid = await verify_email_otp(payload.email, payload.otp)
    if not is_valid:
        return {"verified": False, "reason": "Invalid or expired OTP"}

    access_token = create_access_token(payload.email)
    refresh_token = create_refresh_token(payload.email)

    return {
        "verified": True,
        "access_token": access_token,
        "refresh_token": refresh_token
    }
@router.post("/signup")
async def signup_user(data: UserSignupRequest):
    exists = await check_user_by_email(data.email)
    if exists:
        raise HTTPException(status_code=409, detail="User already exists")

    uid = await create_user_document(data)
    return { "message": "User registered successfully", "uid": uid }


@router.post("/refresh-token")
async def refresh_token(payload: RefreshTokenRequest):
    email = verify_token(payload.refresh_token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(email)
    return { "access_token": new_access_token }