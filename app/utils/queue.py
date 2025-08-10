import os
import json
from datetime import datetime, timezone
import boto3

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["ALLY_EMAIL_QUEUE_URL"]

def enqueue_ally_email_job(
    user_email: str,
    ally_email: str,
    address_text: str,
    lat: float,
    lng: float,
    sos_timestamp: str,
):
    message = {
        "type": "ALLY_SOS_EMAIL",
        "user_email": user_email,
        "ally_email": ally_email,
        "address": address_text,
        "lat": lat,
        "lng": lng,
        "sos_timestamp": sos_timestamp,
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
    }
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message)
    )