from fastapi import APIRouter, HTTPException, Query
from app.schemas.user_schemas import UserSignupRequest, OTPVerifyRequest, EmailRequest, RefreshTokenRequest, \
    UpdateUserProfile
from app.utils.auth import  create_access_token, create_refresh_token, verify_token
from app.utils.db import check_user_by_email, create_user_document, generate_and_store_email_otp, verify_email_otp
from app.utils.email import send_otp_email
from app.utils.db import get_dynamodb_table
from fastapi.responses import JSONResponse
router = APIRouter(prefix="/user", tags=["User"])
user_table = get_dynamodb_table("users")

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

    response = JSONResponse(content={
        "verified": True,
        "access_token": access_token,
    })

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,               # only over HTTPS in production
        samesite="strict",         # can adjust to 'lax' if cross-site login is needed
        max_age=15*24*60*60         # expires in 15 days
    )

    return response
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

@router.get("/profile")
async def get_user_profile(email: str = Query(...)):
    response = user_table.get_item(Key={"email": email})
    user = response.get("Item")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.patch("/editprofile")
async def update_user_profile(data: UpdateUserProfile):
    update_expr = []
    expr_attr_values = {}
    expr_attr_names = {}

    if data.name is not None:
        update_expr.append("#name = :name")
        expr_attr_names["#name"] = "name"
        expr_attr_values[":name"] = data.name

    if data.phone is not None:
        update_expr.append("phone = :phone")
        expr_attr_values[":phone"] = data.phone

    if data.whatsapp_opt_in is not None:
        update_expr.append("whatsapp_opt_in = :opt")
        expr_attr_values[":opt"] = data.whatsapp_opt_in

    if data.home_address is not None:
        update_expr.append("home_address = :addr")
        expr_attr_values[":addr"] = data.home_address

    if not update_expr:
        raise HTTPException(status_code=400, detail="No fields to update")

    user_table.update_item(
        Key={"email": data.email},
        UpdateExpression="SET " + ", ".join(update_expr),
        ExpressionAttributeNames=expr_attr_names if expr_attr_names else None,
        ExpressionAttributeValues=expr_attr_values
    )

    return {"message": "Profile updated successfully"}