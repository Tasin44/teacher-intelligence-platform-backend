



import hashlib
import secrets
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
    """Cryptographically-safe 6-digit numeric OTP using secrets module."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def _hash_otp(otp_code: str) -> str:
    """SHA-256 hash of OTP — stored in DB instead of plaintext."""
    return hashlib.sha256(otp_code.encode()).hexdigest()


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
    if len(value) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters long."
        )
    import re
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise serializers.ValidationError(
            "Password must contain at least one letter and one number."
        )
    return value


# ─── OTP brute-force protection ─────────────────────────
_OTP_MAX_ATTEMPTS = 5
_OTP_LOCKOUT_SECONDS = 900  # 15 minutes


def _check_otp_rate_limit(identifier: str) -> None:
    """Raise if too many failed OTP attempts for this identifier."""
    key = f"otp_attempts:{identifier}"
    attempts = cache.get(key, 0)
    if attempts >= _OTP_MAX_ATTEMPTS:
        raise serializers.ValidationError(
            {"otp_code": "Too many failed attempts. Try again in 15 minutes."}
        )


def _record_otp_failure(identifier: str) -> None:
    """Increment failed OTP attempt counter."""
    key = f"otp_attempts:{identifier}"
    attempts = cache.get(key, 0)
    cache.set(key, attempts + 1, timeout=_OTP_LOCKOUT_SECONDS)


def _clear_otp_attempts(identifier: str) -> None:
    """Reset failed OTP counter on success."""
    cache.delete(f"otp_attempts:{identifier}")


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
            otp_code=_hash_otp(otp_code),
            purpose=OTPVerification.Purpose.SIGNUP,
            expires_at=_otp_expiry(minutes=10),
        )

        # Cache pending signup data keyed by hashed otp_code (TTL = 10 min)
        # so the verify step can reconstruct the teacher row without
        # asking the client to re-send sensitive fields.
        cache.set(f"signup_{_hash_otp(otp_code)}", data, timeout=600)

        return otp_code, identifier



# ─────────────────────────────────────────────
# SIGNUP — step 2  (OTP verify → create teacher)
# ─────────────────────────────────────────────
class VerifySignupOTPSerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        otp_code = attrs["otp_code"]
        hashed   = _hash_otp(otp_code)

        try:
            otp = OTPVerification.objects.filter(
                otp_code=hashed,
                purpose=OTPVerification.Purpose.SIGNUP,
                is_verified=False,
            ).latest("created_at")
        except OTPVerification.DoesNotExist:
            _record_otp_failure("signup_global")
            raise serializers.ValidationError({"otp_code": "Invalid OTP."})

        _check_otp_rate_limit(otp.identifier)

        if otp.is_expired():
            raise serializers.ValidationError(
                {"otp_code": "OTP has expired. Please request a new one."})

        pending_data = cache.get(f"signup_{hashed}")
        if not pending_data:
            raise serializers.ValidationError(
                {"otp_code": "Signup session expired. Please sign up again."})

        _clear_otp_attempts(otp.identifier)
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

# ─────────────────────────────────────────────
# FORGOT PASSWORD — step 1  (send OTP)
# ─────────────────────────────────────────────
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.strip().lower()
        # Security: don't reveal if account exists — store teacher privately
        teacher = Teacher.objects.filter(email=value, is_active=True).first()
        # Store as private attr; view decides response regardless
        self._teacher = teacher
        return value

    @transaction.atomic
    def save(self):
        identifier = self.validated_data["email"]

        # Only actually create OTP if teacher exists — caller always gets 200
        if not self._teacher:
            return None, identifier

        OTPVerification.objects.filter(
            identifier=identifier,
            purpose=OTPVerification.Purpose.FORGOT_PASSWORD,
            is_verified=False,
        ).update(is_verified=True)

        otp_code = _generate_otp()
        OTPVerification.objects.create(
            teacher    = self._teacher,
            identifier = identifier,
            otp_code   = _hash_otp(otp_code),
            purpose    = OTPVerification.Purpose.FORGOT_PASSWORD,
            expires_at = _otp_expiry(minutes=10),
        )
        return otp_code, identifier



# ─────────────────────────────────────────────
# FORGOT PASSWORD — step 2  (verify OTP)
# ─────────────────────────────────────────────
class VerifyForgotPasswordOTPSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        identifier = attrs["email"].strip().lower()
        hashed     = _hash_otp(attrs["otp_code"])

        _check_otp_rate_limit(identifier)

        try:
            otp = OTPVerification.objects.get(
                identifier  = identifier,
                otp_code    = hashed,
                purpose     = OTPVerification.Purpose.FORGOT_PASSWORD,
                is_verified = False,
            )
        except OTPVerification.DoesNotExist:
            _record_otp_failure(identifier)
            raise serializers.ValidationError({"otp_code": "Invalid OTP."})

        if otp.is_expired():
            raise serializers.ValidationError({"otp_code": "OTP has expired."})

        _clear_otp_attempts(identifier)
        attrs["_otp"] = otp
        return attrs

    def save(self):
        otp             = self.validated_data["_otp"]
        otp.is_verified = True
        otp.save(update_fields=["is_verified"])
        # Cache a temporary reset window — valid for 15 minutes after OTP verify
        cache.set(f"reset_window:{otp.id}", True, timeout=900)
        # Return otp.id as the reset_token the client sends back in step 3
        return otp


# ─────────────────────────────────────────────
# RESET PASSWORD — step 3
# ─────────────────────────────────────────────
class ResetPasswordSerializer(serializers.Serializer):
    # otp.id returned from verify step
    reset_token      = serializers.IntegerField()
    new_password     = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return _validate_password_strength(value)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."})

        # Verify the reset window is still active (15-minute expiry)
        reset_token = attrs["reset_token"]
        if not cache.get(f"reset_window:{reset_token}"):
            raise serializers.ValidationError(
                {"reset_token": "Reset token has expired. Please start the password reset process again."})

        try:
            otp = OTPVerification.objects.select_related("teacher").get(
                id          = reset_token,
                purpose     = OTPVerification.Purpose.FORGOT_PASSWORD,
                is_verified = True,   # must have been verified in step 2
            )
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError(
                {"reset_token": "Invalid or expired reset token."})

        if not otp.teacher:
            raise serializers.ValidationError({"reset_token": "Teacher not found."})

        attrs["_teacher"] = otp.teacher
        attrs["_otp_id"]  = reset_token
        return attrs

    @transaction.atomic
    def save(self):
        teacher: Teacher = self.validated_data["_teacher"]
        teacher.set_password(self.validated_data["new_password"])
        teacher.save(update_fields=["password", "updated_at"])
        # Consume the reset window so the token can't be reused
        cache.delete(f"reset_window:{self.validated_data['_otp_id']}")
        return teacher


