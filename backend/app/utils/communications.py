from typing import Optional
import random
import string
from datetime import datetime, timedelta
import asyncio

# In-memory storage for verification codes (in production, use Redis or database)
verification_codes = {}

def generate_verification_code(length: int = 6) -> str:
    """Generate a random verification code"""
    return ''.join(random.choices(string.digits, k=length))

async def send_sms(phone_number: str, message: str) -> bool:
    """
    Send SMS message (mock implementation)
    In production, integrate with Twilio, AWS SNS, or similar service
    """
    try:
        # Mock delay to simulate SMS sending
        await asyncio.sleep(0.5)
        
            "system",
            "SMS_SENT",
            {
                "phone_number": phone_number[:3] + "****" + phone_number[-4:],
                "message_length": len(message),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        print(f"[MOCK SMS] To: {phone_number}")
        print(f"[MOCK SMS] Message: {message}")
        
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False

async def send_email(email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send email message (mock implementation)
    In production, integrate with SendGrid, AWS SES, or similar service
    """
    try:
        # Mock delay to simulate email sending
        await asyncio.sleep(0.3)
        
            "system",
            "EMAIL_SENT",
            {
                "email": email.split('@')[0][:3] + "****@" + email.split('@')[1],
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        print(f"[MOCK EMAIL] To: {email}")
        print(f"[MOCK EMAIL] Subject: {subject}")
        print(f"[MOCK EMAIL] Body: {body}")
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def store_verification_code(user_id: int, method: str, code: str, expiry_minutes: int = 10):
    """Store verification code with expiry"""
    key = f"{user_id}:{method}"
    verification_codes[key] = {
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=expiry_minutes),
        "attempts": 0
    }

def verify_code(user_id: int, method: str, code: str) -> tuple[bool, str]:
    """Verify a code and return (success, error_message)"""
    key = f"{user_id}:{method}"
    
    if key not in verification_codes:
        return False, "No verification code found"
    
    stored = verification_codes[key]
    
    # Check expiry
    if datetime.utcnow() > stored["expires_at"]:
        del verification_codes[key]
        return False, "Verification code expired"
    
    # Check attempts
    stored["attempts"] += 1
    if stored["attempts"] > 3:
        del verification_codes[key]
        return False, "Too many attempts"
    
    # Check code
    if stored["code"] == code:
        del verification_codes[key]
        return True, ""
    
    return False, "Invalid verification code"

async def send_2fa_sms(phone_number: str, user_id: int) -> bool:
    """Send 2FA code via SMS"""
    code = generate_verification_code()
    store_verification_code(user_id, "sms", code)
    
    message = f"Your verification code is: {code}. This code expires in 10 minutes."
    return await send_sms(phone_number, message)

async def send_2fa_email(email: str, user_id: int) -> bool:
    """Send 2FA code via email"""
    code = generate_verification_code()
    store_verification_code(user_id, "email", code)
    
    subject = "Your Verification Code"
    body = f"""Your verification code is: {code}

This code expires in 10 minutes.

If you didn't request this code, please ignore this email.
"""
    
    html_body = f"""
<html>
<body>
    <h2>Verification Code</h2>
    <p>Your verification code is:</p>
    <h1 style="font-size: 32px; letter-spacing: 5px; color: #333;">{code}</h1>
    <p>This code expires in 10 minutes.</p>
    <p><small>If you didn't request this code, please ignore this email.</small></p>
</body>
</html>
"""
    
    return await send_email(email, subject, body, html_body)