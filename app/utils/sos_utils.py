from app.utils.db import get_dynamodb_table
from app.utils.maps import reverse_geocode
from app.utils.ally_utils import get_accepted_allies
from app.utils.queue import enqueue_ally_email_job
import asyncio

sos_table = get_dynamodb_table("sos_events")


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


async def enqueue_ally_notifications(email: str, timestamp: str, location: dict):
    lat = location.get("latitude")
    lng = location.get("longitude")
    address = await reverse_geocode(lat, lng)
    allies = get_accepted_allies(email)

    for ally in allies:
        enqueue_ally_email_job(
            user_email=email,
            ally_email=ally,  # pass as string now
            address_text=address,
            lat=lat,
            lng=lng,
            sos_timestamp=timestamp,
        )

async def trigger_sos_with_alert(email: str, location: dict, timestamp: str):
    trigger_sos(email, location, timestamp)
    await enqueue_ally_notifications(email, timestamp, location)


async def update_heartbeat_with_alert(email: str, timestamp: str, location: dict):
    update_heartbeat(email, timestamp, location)
    await enqueue_ally_notifications(email, timestamp, location)


def end_sos(email: str, timestamp: str):
    sos_table.update_item(
        Key={"email": email, "timestamp": timestamp},
        UpdateExpression="SET active = :false",
        ExpressionAttributeValues={":false": False}
    )