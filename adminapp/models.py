from django.db import models


class School(models.Model):
    school_id = models.BigAutoField(primary_key=True)
    school_name = models.CharField(max_length=250)
    region_district_office = models.CharField(max_length=250)
    registration_status = models.CharField(
        max_length=20,
        choices=[("Active", "Active"), ("Pending", "Pending")],
        default="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "schools"
        ordering = ["school_name"]

    def __str__(self):
        return self.school_name


class AIConfiguration(models.Model):
    """
    Singleton model to hold the global AI configuration.
    """
    temperature = models.FloatField(default=0.6)
    max_tokens = models.IntegerField(default=4000)
    ai_model = models.CharField(max_length=50, default="gpt-4o-mini")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_configurations"
        
    @classmethod
    def get_config(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class AIUsageLog(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey("authapp.Teacher", on_delete=models.CASCADE, related_name="ai_usage_logs")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="ai_usage_logs")
    tokens_used = models.IntegerField(default=0)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    endpoint = models.CharField(max_length=100) # e.g., 'assignment_generation', 'analysis_report'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_usage_logs"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["teacher"]),
            models.Index(fields=["school"]),
        ]
