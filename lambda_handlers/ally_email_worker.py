import json
import os
from app.utils.email import send_html_email  # uses your SMTP env vars

SUBJECT_TPL = "GuardianX – SOS Alert from {user_email}"
HTML_TPL = """\
<html><body>
  <h2>SOS Update</h2>
  <p>{user_email} is currently in danger and has triggered an SOS.</p>
  <p><strong>Location:</strong> {address}</p>
  <p>Please take action if needed. This is an automated update from GuardianX.</p>
</body></html>
"""

def _build_email(user_email: str, address: str):
    subject = SUBJECT_TPL.format(user_email=user_email)
    body = HTML_TPL.format(user_email=user_email, address=address)
    return subject, body

def _process_message(msg: dict):
    if msg.get("type") != "ALLY_SOS_EMAIL":
        return  # ignore unknown message types

    ally_email = msg["ally_email"]         # string (one ally per message)
    user_email = msg["user_email"]
    address    = msg["address"]            # human-readable address

    subject, html_body = _build_email(user_email, address)
    # Your util likely handles SMTP via env vars (SMTP_HOST, SMTP_USER, etc.)
    send_html_email(ally_email, subject, html_body)

def handler(event, context):
    # SQS invokes with a batch of up to N messages
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        _process_message(body)