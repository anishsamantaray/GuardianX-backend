import boto3
import time
from boto3.dynamodb.conditions import Key
from app.utils.maps import reverse_geocode
from app.utils.email import send_ally_sos_email
from app.utils.ally_utils import get_accepted_allies
dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
sos_table = dynamodb.Table("sos_events")

def trigger_sos(email: str, location: dict, timestamp: str):
    sos_table.put_item(Item={
        "email": email,
        "timestamp": timestamp,
        "location": location,
        "active": True
    })

def update_heartbeat(email: str, timestamp: str, location: dict):
    sos_table.update_item(
        Key={"email": email, "timestamp": timestamp},
        UpdateExpression="SET location = :loc",
        ExpressionAttributeValues={":loc": location}
    )

async def update_heartbeat_with_alert(email: str, timestamp: str, location: dict):
    # 1. Update SOS
    update_heartbeat(email, timestamp, location)

    # 2. Get address from lat/lng
    address = await reverse_geocode(location["latitude"], location["longitude"])

    # 3. Get all accepted allies
    allies = get_accepted_allies(email)  # returns list of emails

    # 4. Send email to each ally
    for ally_email in allies:
        await send_ally_sos_email(ally_email, email, address)

def end_sos(email: str, timestamp: str):
    sos_table.update_item(
        Key={"email": email, "timestamp": timestamp},
        UpdateExpression="SET active = :false",
        ExpressionAttributeValues={":false": False}
    )
