import boto3
from app.schemas.user_schemas import UserSignupRequest
import time
import random

dynamodb = boto3.resource(
        "dynamodb",
        region_name='ap-south-1',  # Change to your region
        aws_access_key_id='AKIARN33E7O3DYAQNVGT',
        aws_secret_access_key='lbcqRcOcamF8hxT44JgYSj0Hby+NWvqm+gFxx928'
)
user_table = dynamodb.Table("users")
otp_table = dynamodb.Table("otp_requests")

async def check_user_by_email(email: str) -> bool:
    response = user_table.get_item(Key={"email": email})
    return "Item" in response

async def create_user_document(data: UserSignupRequest) -> str:
    user_data = {
        "email": data.email,
        "name": data.name,
        "phone": data.phone,
        "whatsapp_opt_in": data.whatsapp_opt_in,
        "emergency_contacts": [ec.dict() for ec in data.emergency_contacts],
        "home_address": data.home_address.dict()
    }

    user_table.put_item(Item=user_data)
    return data.email

async def generate_and_store_email_otp(email: str) -> str:
    otp = str(random.randint(100000, 999999))
    ttl = int(time.time()) + 300  # expires in 5 minutes

    otp_table.put_item(Item={
        "email": email,
        "otp": otp,
        "ttl": ttl
    })

    return otp

async def verify_email_otp(email: str, otp: str) -> bool:
    response = otp_table.get_item(Key={"email": email})
    item = response.get("Item")

    if not item:
        return False

    if item["otp"] != otp:
        return False

    if item["ttl"] < int(time.time()):
        return False

    # Optional: delete OTP after verification
    otp_table.delete_item(Key={"email": email})
    return True