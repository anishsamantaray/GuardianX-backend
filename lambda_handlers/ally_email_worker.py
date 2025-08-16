import json
import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

# Email template
SUBJECT_TPL = "GuardianX – SOS Alert from {user_email}"
HTML_TPL = """\
<html><body>
  <h2>SOS Update</h2>
  <p>{user_email} is currently in danger and has triggered an SOS.</p>
  <p><strong>Location:</strong> {address}</p>
  <p>Please take action if needed. This is an automated update from GuardianX.</p>
</body></html>
"""

# Send email using SMTP
def send_html_email(to_email, subject, html_body):
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    from_email = os.environ.get("SMTP_FROM", username)
    from_name = os.environ.get("SMTP_FROM_NAME", "GuardianX")

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_email))
    msg["To"] = to_email

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.sendmail(from_email, [to_email], msg.as_string())

# Build and send the ally email
def _process_message(msg):
    if msg.get("type") != "ALLY_SOS_EMAIL":
        return

    user_email = msg["user_email"]
    ally_email = msg["ally_email"]
    address = msg["address"]

    subject = SUBJECT_TPL.format(user_email=user_email)
    body = HTML_TPL.format(user_email=user_email, address=address)
    send_html_email(ally_email, subject, body)

# Lambda handler
def handler(event, context):
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        _process_message(body)