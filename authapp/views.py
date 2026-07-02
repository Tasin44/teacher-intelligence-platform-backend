from django.db.models.lookups import IntegerLessThanOrEqual
from rest_framework import permissions
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


# ─────────────────────────────────────────────
# ME
# GET /api/auth/me
# ─────────────────────────────────────────────
class MeView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request):
        return self.success_response(
            data    = TeacherPublicSerializer(request.user).data,
            message = "Profile fetched successfully.",
        )

# ─────────────────────────────────────────────
# FORGOT PASSWORD — step 1  (send OTP)
# POST /api/auth/forgot-password
# ─────────────────────────────────────────────
class ForgotPasswordView(StandardResponseMixin, APIView):
    """
    Always returns 200 to avoid revealing whether the email is registered
    (prevents account enumeration attacks).
    """
    permission_classes = [AllowAny]
    throttle_scope     = "auth"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        # We handle errors manually (not raise_exception=True) so we can
        # always return 200 and never leak whether an account exists.
        if not serializer.is_valid():
            # Only real validation error here is a malformed email field
            if "email" in serializer.errors and "already exists" not in str(serializer.errors):
                return self.error_response(
                    "Validation Error",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    serializer.errors,
                )

        otp_code, identifier = serializer.save()

        if otp_code:
            _send_otp(identifier, otp_code, "forgot_password")

        return self.success_response(
            data    = {},
            message = "If an account with this email exists, an OTP has been sent.",
        )


# ─────────────────────────────────────────────
# FORGOT PASSWORD — step 2  (verify OTP)
# POST /api/auth/forgot-password/verify
# ─────────────────────────────────────────────
class VerifyForgotPasswordOTPView(StandardResponseMixin, APIView):
    permission_classes = [AllowAny]
    throttle_scope     = "auth"

    def post(self, request):
        serializer = VerifyForgotPasswordOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                "OTP verification failed",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                serializer.errors,
            )
        otp = serializer.save()

        return self.success_response(
            data    = {"reset_token": otp.id},
            message = "OTP verified. Proceed to reset your password.",
        )


# ─────────────────────────────────────────────
# RESET PASSWORD — step 3
# POST /api/auth/reset-password
# ─────────────────────────────────────────────
class ResetPasswordView(StandardResponseMixin, APIView):
    permission_classes = [AllowAny]
    throttle_scope     = "auth"

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                "Password reset failed",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                serializer.errors,
            )
        serializer.save()

        return self.success_response(
            data    = {},
            message = "Password reset successfully. Please log in.",
        )