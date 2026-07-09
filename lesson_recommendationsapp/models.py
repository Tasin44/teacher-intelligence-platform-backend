from django.db import models

# Create your models here.
from django.db import models


class LessonRecommendation(models.Model):
    class Status(models.TextChoices):
        PENDING  = "pending",  "Pending"
        APPLIED  = "applied",  "Applied"
        DISMISSED = "dismiss", "Dismissed"

    class AppliedTargetType(models.TextChoices):
        GROUP   = "group",   "Group"
        STUDENT = "student", "Student"

    lesson_rec_id          = models.BigAutoField(primary_key=True)
    assignment             = models.ForeignKey("assignments.Assignment", on_delete=models.CASCADE,related_name="lesson_recommendations")
    recommendation_date    = models.DateTimeField(auto_now_add=True)
    recommendation_details = models.TextField()

    applied_target_type  = models.CharField(max_length=10,choices=AppliedTargetType.choices,null=True, blank=True)
    applied_student      = models.ForeignKey("students.Student", on_delete=models.SET_NULL,null=True, blank=True,related_name="lesson_recommendations")
    applied_group        = models.ForeignKey("groups.Group", on_delete=models.SET_NULL,null=True, blank=True,related_name="lesson_recommendations")
    status               = models.CharField(max_length=10, choices=Status.choices,default=Status.PENDING)

    class Meta:
        db_table = "lesson_recommendations"
        indexes  = [models.Index(fields=["assignment", "status"])]
        ordering = ["-recommendation_date"]