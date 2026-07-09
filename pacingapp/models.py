from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class PacingRecommendation(models.Model):
    pacing_id                    = models.BigAutoField(primary_key=True)
    teacher                      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="pacing_recommendations")
    assignment                   = models.ForeignKey("assignmentapp.Assignment", on_delete=models.CASCADE,related_name="pacing_recommendations",null=True, blank=True)
    topic                        = models.CharField(max_length=200)
    # AI outputs
    curriculum_adjustment        = models.TextField()   # narrative AI recommendation
    standards_coverage_checklist = models.JSONField(default=list)  # [{standard, covered: bool, notes}]
    generated_at                 = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pacing_recommendations"
        ordering = ["-generated_at"]
        indexes  = [models.Index(fields=["teacher", "topic"])]