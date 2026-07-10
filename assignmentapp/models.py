from django.db import models

# Create your models here.
import uuid
from django.conf import settings
from django.db import models


class Assignment(models.Model):
    class TargetType(models.TextChoices):
        ALL_GROUPS = "all_groups", "All Groups"
        STUDENT = "individual_student", "Individual Student"
        GROUP = "individual_group", "Individual Group"

    class Difficulty(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    assignment_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="assignments", db_index=True)
    title = models.CharField(max_length=200, db_index=True)
    subject = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=25, choices=TargetType.choices)
    target_student = models.ForeignKey("studentapp.Student", on_delete=models.SET_NULL,null=True, blank=True, related_name="targeted_assignments")
    target_group = models.ForeignKey("groupapp.Group", on_delete=models.SET_NULL,null=True, blank=True, related_name="targeted_assignments")
    ai_difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    ccss_code = models.CharField(max_length=50, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    instructions = models.TextField(blank=True, null=True)
    number_of_questions = models.PositiveIntegerField(default=5)
    unique_assignment_code = models.CharField(max_length=50, unique=True, editable=False)
    tag = models.CharField(max_length=100, blank=True, null=True)
    ai_generation_status = models.CharField(
        max_length=15,
        choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assignments"
        indexes = [
            models.Index(fields=["teacher", "title"]),
            models.Index(fields=["teacher", "due_date"]),
            models.Index(fields=["teacher", "subject"]),
        ]
        ordering = ["-creation_date"]

    def save(self, *args, **kwargs):
        if not self.unique_assignment_code:
            self.unique_assignment_code = f"AS-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} [{self.unique_assignment_code}]"

class AssignmentQuestion(models.Model):
    question_id = models.BigAutoField(primary_key=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    question_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "assignment_questions"
        ordering = ["question_order"]


class AssignmentMailLog(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="mail_logs")
    student = models.ForeignKey("studentapp.Student", on_delete=models.CASCADE, related_name="assignment_mails")
    parent_email = models.EmailField(max_length=150)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignment_mail_log"

class AssignmentSubmission(models.Model):
    submission_id = models.BigAutoField(primary_key=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student_name = models.CharField(max_length=200)
    roll_number = models.CharField(max_length=50)
    grade = models.CharField(max_length=50)
    parent_name = models.CharField(max_length=200)
    attachment = models.FileField(upload_to="assignment_submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignment_submissions"
        ordering = ["-submitted_at"]