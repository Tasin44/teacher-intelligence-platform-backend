from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class Intervention(models.Model):
    class TargetType(models.TextChoices):
        STUDENT = "individual_student", "Individual Student"
        GROUP   = "individual_group",   "Individual Group"

    intervention_id   = models.BigAutoField(primary_key=True)
    teacher           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="interventions", db_index=True)
    target_type       = models.CharField(max_length=20, choices=TargetType.choices)

    # Student target fields
    student           = models.ForeignKey("students.Student", on_delete=models.CASCADE,null=True, blank=True, related_name="interventions")
    # Group target fields
    group             = models.ForeignKey("groups.Group", on_delete=models.CASCADE,null=True, blank=True, related_name="interventions")

    intervention_type = models.TextField()
    reason            = models.TextField()
    start_date        = models.DateField()
    frequency         = models.CharField(max_length=100)
    notes             = models.TextField(blank=True, null=True)

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "interventions"
        indexes  = [
            models.Index(fields=["teacher", "target_type"]),
            models.Index(fields=["student"]),
            models.Index(fields=["group"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(target_type="individual_student",student__isnull=False, group__isnull=True) |
                    models.Q(target_type="individual_group",group__isnull=False, student__isnull=True)
                ),
                name="chk_intervention_target_consistency",
            )
        ]
        ordering = ["-created_at"]
