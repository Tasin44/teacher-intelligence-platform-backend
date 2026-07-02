from django.shortcuts import render

# Create your views here.
from coreapp.response import StandardResponseMixin
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    TeacherPublicSerializer,
    SignupSerializer,
    VerifySignupOTPSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    VerifyForgotPasswordOTPSerializer,
    ResetPasswordSerializer,
)
from rest_framework import status



# ── placeholder: swap with SendGrid/SES/Twilio in production ────────────────
def _send_otp(identifier: str, otp_code: str, purpose: str):
    """Send OTP email. Replace with real email service in production."""
    print(f"[OTP] Sending {purpose} OTP {otp_code!r} to {identifier}")



# ─────────────────────────────────────────────
# SIGNUP — step 1
# POST /api/auth/signup
# ─────────────────────────────────────────────
class SignupView(StandardResponseMixin, APIView):
    """
    Validates teacher info, stores pending data in Redis,
    sends a 6-digit OTP to the given email.
    Teacher row is NOT created yet.
    """
    permission_classes = [AllowAny]
    throttle_scope     = "auth"

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                "Signup failed",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                serializer.errors,
            )
        otp_code, identifier = serializer.save()
        _send_otp(identifier, otp_code, "signup")

        return self.success_response(
            data    = {"identifier": identifier},
            message = "OTP sent to your email. Please verify within 10 minutes.",
        )


# ─────────────────────────────────────────────
# SIGNUP — step 2  (OTP verify → create teacher)
# POST /api/auth/signup/verify
# ─────────────────────────────────────────────
class VerifySignupOTPView(StandardResponseMixin, APIView):
    """
    Verifies OTP → creates Teacher row → returns JWT tokens.
    """
    permission_classes = [AllowAny]
    throttle_scope     = "auth"

    def post(self, request):
        serializer = VerifySignupOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                "OTP verification failed",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                serializer.errors,
            )
        teacher, tokens = serializer.save() # cause on the verifysignupotpserializer, it's returning teacher, token

        return self.success_response(
            data = {
                "teacher": TeacherPublicSerializer(teacher).data,
                "tokens":  tokens,
            },
            message     = "Account created successfully.",
            status_code = status.HTTP_201_CREATED,
        )

# ─────────────────────────────────────────────
# LOGIN
# POST /api/auth/login
# ─────────────────────────────────────────────
class LoginView(StandardResponseMixin, APIView):
    permission_classes = [AllowAny]
    throttle_scope     = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                "Login failed",
                status.HTTP_401_UNAUTHORIZED,
                serializer.errors,
            )
        teacher, tokens = serializer.save()

        return self.success_response(
            data    = {"teacher": TeacherPublicSerializer(teacher).data, "tokens": tokens},
            message = "Login successful.",
        )



