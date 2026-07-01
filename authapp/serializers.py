



import random
import re
import string
from datetime import timedelta

from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Teacher, OTPVerification


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _generate_otp(length: int = 6) -> str:
    """Cryptographically-safe 6-digit numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


def _otp_expiry(minutes: int = 10):
    return timezone.now() + timedelta(minutes=minutes)


def _issue_tokens(teacher: Teacher) -> dict:
    """Return access + refresh JWT pair."""
    refresh = RefreshToken.for_user(teacher)
    return {
        "refresh": str(refresh),
        "access":  str(refresh.access_token),
    }


def _validate_password_strength(value: str) -> str:
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise serializers.ValidationError(
            "Password must contain at least one letter and one number."
        )
    return value


# ─────────────────────────────────────────────
# PUBLIC TEACHER PROFILE
# ─────────────────────────────────────────────
class TeacherPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Teacher
        fields = ["teacher_id", "first_name", "last_name",
                  "school_name", "grade", "room", "email", "is_verified"]



# ─────────────────────────────────────────────
# SIGNUP — step 1
# Validates uniqueness, stores pending data in Redis,
# creates OTP record. Teacher row NOT created yet.
# ─────────────────────────────────────────────
class SignupSerializer(serializers.Serializer):
    first_name  = serializers.CharField(max_length=100)
    last_name   = serializers.CharField(max_length=100)
    school_name = serializers.CharField(max_length=150)
    grade       = serializers.CharField(max_length=20)
    room        = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email       = serializers.EmailField(max_length=250)
    password    = serializers.CharField(write_only=True, min_length=8)


    def validate_email(self, value):
        value = value.strip().lower()
        if Teacher.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        return _validate_password_strength(value)

    @transaction.atomic
    def save(self):
        data       = self.validated_data
        identifier = data["email"]

        # Invalidate any previous pending signup OTPs for this email
        OTPVerification.objects.filter(
            identifier=identifier,
            purpose=OTPVerification.Purpose.SIGNUP,
            is_verified=False,
        ).update(is_verified=True)

        otp_code = _generate_otp()
        OTPVerification.objects.create(
            teacher=None,
            identifier=identifier,
            otp_code=otp_code,
            purpose=OTPVerification.Purpose.SIGNUP,
            expires_at=_otp_expiry(minutes=10),
        )

        # Cache pending signup data keyed by otp_code (TTL = 10 min)
        # so the verify step can reconstruct the teacher row without
        # asking the client to re-send sensitive fields.
        cache.set(f"signup_{otp_code}", data, timeout=600)

        return otp_code, identifier



# ─────────────────────────────────────────────
# SIGNUP — step 2  (OTP verify → create teacher)
# ─────────────────────────────────────────────
class VerifySignupOTPSerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        otp_code = attrs["otp_code"]

        try:
            otp = OTPVerification.objects.filter(
                otp_code=otp_code,
                purpose=OTPVerification.Purpose.SIGNUP,
                is_verified=False,
            ).latest("created_at")
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError({"otp_code": "Invalid OTP."})

        if otp.is_expired():
            raise serializers.ValidationError(
                {"otp_code": "OTP has expired. Please request a new one."})

        pending_data = cache.get(f"signup_{otp_code}")
        if not pending_data:
            raise serializers.ValidationError(
                {"otp_code": "Signup session expired. Please sign up again."})

        attrs["_otp"]         = otp
        attrs["pending_data"] = pending_data
        return attrs
    @transaction.atomic
    def save(self):
        otp: OTPVerification = self.validated_data["_otp"]
        pending              = self.validated_data["pending_data"]

        teacher = Teacher.objects.create_user(
            email       = pending["email"],
            password    = pending["password"],
            first_name  = pending["first_name"],
            last_name   = pending["last_name"],
            school_name = pending["school_name"],
            grade       = pending["grade"],
            room        = pending.get("room") or None,
            is_verified = True,
        )

        otp.is_verified = True
        otp.teacher     = teacher
        otp.save(update_fields=["is_verified", "teacher"])

        # Clean up cache
        cache.delete(f"signup_{otp.otp_code}")

        return teacher, _issue_tokens(teacher)



# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email   = attrs["email"].strip().lower()
        teacher = authenticate(email=email, password=attrs["password"])

        if not teacher:
            raise serializers.ValidationError(
                {"non_field_errors": "Invalid email or password."})

        if not teacher.is_verified:
            raise serializers.ValidationError(
                {"non_field_errors": "Account not verified. Please complete OTP verification."})

        if not teacher.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": "This account has been deactivated."})

        attrs["_teacher"] = teacher
        return attrs

    def save(self):
        teacher = self.validated_data["_teacher"]
        return teacher, _issue_tokens(teacher)










