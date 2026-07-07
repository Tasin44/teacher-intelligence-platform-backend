from django.db import models

# Create your models here.
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone

# ─────────────────────────────────────────────
# CUSTOM USER MANAGER
# ─────────────────────────────────────────────
class TeacherManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email).lower()
        teacher = self.model(email=email, **extra_fields)
        teacher.set_password(password)
        teacher.save(using=self._db)
        return teacher

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        return self.create_user(email, password, **extra_fields)


# ─────────────────────────────────────────────
# TEACHER (custom user model)
# ─────────────────────────────────────────────
class Teacher(AbstractBaseUser, PermissionsMixin):
    teacher_id  = models.BigAutoField(primary_key=True)
    first_name  = models.CharField(max_length=100)
    last_name   = models.CharField(max_length=100)
    school      = models.ForeignKey("adminapp.School", on_delete=models.SET_NULL, null=True, related_name="teachers")
    grade       = models.CharField(max_length=20)
    room        = models.CharField(max_length=50, blank=True, null=True)
    email       = models.EmailField(max_length=250, unique=True)

    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    # False until the teacher verifies the OTP sent during signup
    is_verified = models.BooleanField(default=False)
    
    APPROVAL_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default="pending")

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    objects = TeacherManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "grade"]

    class Meta:
        db_table = "teachers"
        indexes  = [models.Index(fields=["email"])]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"



# ─────────────────────────────────────────────
# OTP VERIFICATION
# ─────────────────────────────────────────────
class OTPVerification(models.Model):
    """
    Handles all OTP flows:
    - signup          → teacher is NULL (row doesn't exist yet)
    - forgot_password → teacher is set
    """

    class Purpose(models.TextChoices):
        SIGNUP          = "signup",          "Signup"
        FORGOT_PASSWORD = "forgot_password", "Forgot Password"

    # NULL during signup because the teacher row doesn't exist yet
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="otps",
    )
    # The email the OTP was sent to
    identifier = models.EmailField(max_length=250)
    otp_code   = models.CharField(max_length=6)
    purpose    = models.CharField(max_length=30, choices=Purpose.choices)
    is_verified = models.BooleanField(default=False)
    expires_at  = models.DateTimeField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_verifications"
        indexes  = [
            models.Index(fields=["otp_code"]),
            models.Index(fields=["identifier"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP({self.purpose}) → {self.identifier}"








