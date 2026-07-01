



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





















