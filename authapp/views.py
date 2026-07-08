from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from coreapp.response import StandardResponseMixin
from .serializers import (
    TeacherPublicSerializer,
    TeacherProfileUpdateSerializer,
    SignupSerializer,
    VerifySignupOTPSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    VerifyForgotPasswordOTPSerializer,
    ResetPasswordSerializer,
)



from django.core.mail import send_mail
from django.conf import settings

# ── SendGrid/SES/Twilio or Django SMTP ──────────────────────────────────────
def _send_otp(identifier: str, otp_code: str, purpose: str):
    #    print(f"[OTP] Sending {purpose} OTP {otp_code!r} to {identifier}")
    """Send OTP email using Django's email backend."""
    if purpose == "signup":
        subject = "EduPulse - Verify your email"
        message = f"Welcome to EduPulse! Your email verification OTP is: {otp_code}\n\nThis OTP will expire in 10 minutes."
    elif purpose == "forgot_password":
        subject = "EduPulse - Password Reset Request"
        message = f"We received a request to reset your password. Your OTP is: {otp_code}\n\nThis OTP will expire in 10 minutes. If you did not request this, please ignore this email."
    else:
        subject = "EduPulse - OTP Verification"
        message = f"Your OTP is: {otp_code}"

    try:
        send_mail(
            subject,
            message,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@edupulse.com"),
            [identifier],
            fail_silently=True,
        )
        print(f"[OTP] Successfully sent {purpose} OTP to {identifier}")
    except Exception as e:
        print(f"[OTP Error] Failed to send {purpose} OTP to {identifier}: {e}")



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
    authentication_classes = []
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
    authentication_classes = []
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
                "teacher": TeacherPublicSerializer(teacher, context={"request": request}).data,
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
    authentication_classes = []
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
            data    = {"teacher": TeacherPublicSerializer(teacher, context={"request": request}).data, "tokens": tokens},
            message = "Login successful.",
        )


# ─────────────────────────────────────────────
# ME
# GET /api/auth/me
# ─────────────────────────────────────────────
class MeView(StandardResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"
    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        return self.success_response(
            data    = TeacherPublicSerializer(request.user, context={"request": request}).data,
            message = "Profile fetched successfully.",
        )

    def patch(self, request):
        serializer = TeacherProfileUpdateSerializer(
            instance=request.user, 
            data=request.data, 
            partial=True
        )
        if not serializer.is_valid():
            return self.error_response(
                "Profile update failed",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                serializer.errors,
            )
        teacher = serializer.save()
        
        return self.success_response(
            data    = TeacherPublicSerializer(teacher, context={"request": request}).data,
            message = "Profile updated successfully.",
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
    authentication_classes = []
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
    authentication_classes = []
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
    authentication_classes = []
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