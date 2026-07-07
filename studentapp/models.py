from django.conf import settings
from django.db import models


class Student(models.Model):
    class Risk(models.TextChoices):
        ON_TRACK = "on_track", "On Track"
        AT_RISK = "at_risk", "At Risk"
        ADVANCE = "advance", "Advance"
        DEVELOPING = "developing", "Developing"

    student_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="students", db_index=True)
    student_name = models.CharField(max_length=150)
    student_image = models.URLField(max_length=255, blank=True, null=True)
    student_roll = models.CharField(max_length=50)
    student_grade = models.CharField(max_length=20)
    risk_status = models.CharField(max_length=20, choices=Risk.choices, default=Risk.ON_TRACK)
    reading_level = models.CharField(max_length=20, blank=True, null=True)
    parent_name = models.CharField(max_length=150, blank=True, null=True)
    parent_email = models.EmailField(max_length=150, blank=True, null=True)

    # Denormalized rollups -- intentionally duplicated from feedback/attendance
    # tables so dashboard/list endpoints avoid expensive JOIN+AGG on every
    # request. Kept in sync via signals (see feedback/attendance apps).
    avg_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recommended_group = models.ForeignKey("groupapp.Group", on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name="recommended_students")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "students"
        constraints = [
            models.UniqueConstraint(fields=["teacher", "student_roll"], name="uq_teacher_roll")
        ]
        indexes = [
            models.Index(fields=["teacher", "risk_status"]),
            models.Index(fields=["teacher", "student_name"]),
        ]
        ordering = ["student_name"]

    def __str__(self):
        return f"{self.student_name} ({self.student_roll})"