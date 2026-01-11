from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    Response,
    Depends
)
from fastapi.responses import JSONResponse
from decimal import Decimal
import boto3, uuid

from boto3.dynamodb.conditions import Attr

from app.schemas.user_schemas import (
    UserSignupRequest,
    OTPVerifyRequest,
    EmailRequest,
    UpdateUserProfile
)
from app.utils.auth import (
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.utils.db import (
    check_user_by_email,
    create_user_document,
    generate_and_store_email_otp,
    verify_email_otp,
    get_dynamodb_table
)
from app.utils.email import send_otp_email
from app.core.auth import get_current_user


router = APIRouter(prefix="/user", tags=["User"])
user_table = get_dynamodb_table("users")

@router.post("/send-otp")
async def send_otp(payload: EmailRequest):
    exists = await check_user_by_email(payload.email)

    if exists:
        otp = await generate_and_store_email_otp(payload.email)
        await send_otp_email(payload.email, otp)
        return {"exists": True, "otp_sent": True}

    return {"exists": False}


@router.post("/verify-otp")
async def verify_otp(payload: OTPVerifyRequest):
    is_valid = await verify_email_otp(payload.email, payload.otp)
    if not is_valid:
        return {"verified": False, "reason": "Invalid or expired OTP"}

    access_token = create_access_token(payload.email)
    refresh_token = create_refresh_token(payload.email)

    response = JSONResponse(
        content={
            "verified": True,
            "access_token": access_token
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=15 * 24 * 60 * 60
    )

    return response


@router.post("/signup")
async def signup_user(data: UserSignupRequest):
    exists = await check_user_by_email(data.email)
    if exists:
        raise HTTPException(status_code=409, detail="User already exists")

    uid = await create_user_document(data)
    return {"message": "User registered successfully", "uid": uid}


@router.get("/refresh-token")
async def refresh_token(request: Request):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(email)
    return {"access_token": new_access_token}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return {"detail": "logged out"}

@router.get("/profile")
async def get_user_profile(
    email: str = Depends(get_current_user)
):
    resp = user_table.get_item(Key={"email": email})
    user = resp.get("Item")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.patch("/editprofile")
async def update_user_profile(
    data: UpdateUserProfile,
    email: str = Depends(get_current_user)
):
    update_expr = []
    expr_attr_values = {}
    expr_attr_names = {}

    def convert_floats(obj):
        if isinstance(obj, float):
            return Decimal(str(obj))
        if isinstance(obj, dict):
            return {k: convert_floats(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert_floats(i) for i in obj]
        return obj

    if data.name is not None:
        update_expr.append("#nm = :name")
        expr_attr_names["#nm"] = "name"
        expr_attr_values[":name"] = data.name

    if data.phone is not None:
        update_expr.append("phone = :phone")
        expr_attr_values[":phone"] = data.phone

    if data.whatsapp_opt_in is not None:
        update_expr.append("whatsapp_opt_in = :opt")
        expr_attr_values[":opt"] = data.whatsapp_opt_in

    if data.home_address is not None:
        update_expr.append("home_address = :addr")
        expr_attr_values[":addr"] = convert_floats(data.home_address.dict())

    if not update_expr:
        raise HTTPException(status_code=400, detail="No fields to update")

    user_table.update_item(
        Key={"email": email},
        UpdateExpression="SET " + ", ".join(update_expr),
        ExpressionAttributeValues=expr_attr_values,
        ExpressionAttributeNames=expr_attr_names or None
    )

    return {"message": "Profile updated successfully"}


@router.post("/upload-profile-pic")
async def upload_profile_picture(
    filename: str = Query(...),
    email: str = Depends(get_current_user)
):
    bucket_name = "guardianx-profile-pics"

    unique_id = uuid.uuid4().hex
    key = f"profile_pics/{unique_id}_{filename}"

    s3 = boto3.client("s3")

    try:
        presigned_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket_name,
                "Key": key,
                "ContentType": "image/jpeg"
            },
            ExpiresIn=300
        )

        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"

        user_table.update_item(
            Key={"email": email},
            UpdateExpression="SET dpS3Url = :url",
            ExpressionAttributeValues={":url": s3_url}
        )

        return {
            "uploadUrl": presigned_url,
            "dpS3Url": s3_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_email_suggestions(
    query: str = Query(..., min_length=3),
    _: str = Depends(get_current_user)
):
    try:
        resp = user_table.scan(
            ProjectionExpression="email, #nm",
            ExpressionAttributeNames={"#nm": "name"},
            FilterExpression=(
                Attr("email").contains(query.lower()) |
                Attr("name").contains(query)
            )
        )

        suggestions = [
            {"email": i["email"], "name": i.get("name", "")}
            for i in resp.get("Items", [])
        ]

        while "LastEvaluatedKey" in resp:
            resp = user_table.scan(
                ProjectionExpression="email, #nm",
                ExpressionAttributeNames={"#nm": "name"},
                FilterExpression=(
                    Attr("email").contains(query.lower()) |
                    Attr("name").contains(query)
                ),
                ExclusiveStartKey=resp["LastEvaluatedKey"]
            )
            suggestions.extend([
                {"email": i["email"], "name": i.get("name", "")}
                for i in resp.get("Items", [])
            ])

        return {"suggestions": suggestions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
