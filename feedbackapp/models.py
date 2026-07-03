from django.db import models

# Create your models here.
from django.db import models


class AssignmentFeedback(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GRADED = "graded", "Graded"
        REVIEWED = "reviewed", "Reviewed"

    feedback_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE,related_name="assignment_feedback", db_index=True)
    assignment = models.ForeignKey("assignments.Assignment", on_delete=models.SET_NULL,null=True, blank=True, related_name="feedback_entries")
    subject = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=200)
    score = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    ccss_code = models.CharField(max_length=50, blank=True, null=True)
    assessment_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.GRADED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assignment_feedback"
        indexes = [
            models.Index(fields=["student", "subject"]),
            models.Index(fields=["student", "assessment_date"]),
        ]
        ordering = ["-assessment_date"]
