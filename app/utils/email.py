import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

async def send_otp_email(email: str, otp: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your GuardianX OTP Code"
    msg["From"] = SMTP_USER
    msg["To"] = email

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #2c3e50;">GuardianX Verification</h2>
            <p style="font-size: 16px; color: #333;">Hello,</p>
            <p style="font-size: 16px; color: #333;">
                Your OTP code is:
                <span style="display: inline-block; font-size: 24px; font-weight: bold; background: white; padding: 8px 16px; border-radius: 6px; margin-top: 10px;">
                {otp}
                </span>
            </p>
            <p style="font-size: 14px; color: #666;">This code is valid for 5 minutes.</p>
            <p style="font-size: 14px; color: #666;">If you didn’t request this, you can safely ignore this email.</p>
            <hr style="margin-top: 30px;">
            <p style="font-size: 12px; color: #aaa; text-align: center;">– Team GuardianX</p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, email, msg.as_string())