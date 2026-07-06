from django.conf import settings
from django.db import models


class OffDay(models.Model):
    off_day_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="off_days")
    off_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "off_days"
        constraints = [models.UniqueConstraint(fields=["teacher", "off_date"], name="uq_teacher_offday")]

class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"

    attendance_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE,related_name="attendance_records", db_index=True)
    attendance_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attendance"
        constraints = [models.UniqueConstraint(fields=["student", "attendance_date"],name="uq_student_date")]
        indexes = [models.Index(fields=["student", "attendance_date"])]
        ordering = ["-attendance_date"]