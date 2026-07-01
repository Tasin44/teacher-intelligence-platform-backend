from django.shortcuts import render

# Create your views here.


# ── placeholder: swap with SendGrid/SES/Twilio in production ────────────────
def _send_otp(identifier: str, otp_code: str, purpose: str):
    """Send OTP email. Replace with real email service in production."""
    print(f"[OTP] Sending {purpose} OTP {otp_code!r} to {identifier}")