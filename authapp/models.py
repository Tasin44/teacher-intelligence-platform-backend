from django.db import models

# Create your models here.
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin


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
    school_name = models.CharField(max_length=150)
    grade       = models.CharField(max_length=20)
    room        = models.CharField(max_length=50, blank=True, null=True)
    email       = models.EmailField(max_length=250, unique=True)

    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    # False until the teacher verifies the OTP sent during signup
    is_verified = models.BooleanField(default=False)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    objects = TeacherManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "school_name", "grade"]

    class Meta:
        db_table = "teachers"
        indexes  = [models.Index(fields=["email"])]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"












