from django.db import models
from django.conf import settings


class Group(models.Model):
    class Classification(models.TextChoices):
        ADVANCE = "advance", "Advance"
        ON_TRACK = "on_track", "On Track"
        DEVELOPING = "developing", "Developing"
        RISK = "risk", "Risk"

    class Tag(models.TextChoices):
        ABOVE = "above_grade_level", "Above Grade Level"
        AT = "at_grade_level", "At Grade Level"
        APPROACHING = "approaching_grade_level", "Approaching Grade Level"
        BELOW = "below_grade_level", "Below Grade Level"

    group_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="student_groups", db_index=True)
    group_name = models.CharField(max_length=100)
    classification = models.CharField(max_length=20, choices=Classification.choices)
    tag = models.CharField(max_length=30, choices=Tag.choices)
    avg_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_students = models.PositiveIntegerField(default=0)
    generated_by_ai = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "groups_tbl"
        indexes = [models.Index(fields=["teacher", "classification"])]
        ordering = ["group_name"]

    def __str__(self):
        return self.group_name

class GroupStudent(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="group_memberships")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "group_students"
        unique_together = ("group", "student")