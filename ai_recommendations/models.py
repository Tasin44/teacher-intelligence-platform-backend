from django.db import models

# Create your models here.
from django.db import models


class AIRecommendation(models.Model):
    recommendation_id      = models.BigAutoField(primary_key=True)
    student                = models.ForeignKey("studentapp.Student", on_delete=models.CASCADE,related_name="ai_recommendations", db_index=True)
    current_strengths      = models.TextField()       # 5 bullet points
    recommended_activities = models.TextField()       # 5 bullet points
    skill_gaps             = models.TextField()       # 5 bullet points
    generated_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_recommendations"
        # Keep history; latest per student is the one with highest pk
        ordering = ["-generated_at"]
        indexes  = [models.Index(fields=["student", "-generated_at"])]