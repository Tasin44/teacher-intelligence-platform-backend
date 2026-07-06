from django.db import models



class BehaviorFeedback(models.Model):
    class Classification(models.TextChoices):
        POSITIVE = "positive", "Positive"
        NEUTRAL = "neutral", "Neutral"
        CONCERN = "concern", "Concern"

    behavior_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE,related_name="behavior_feedback", db_index=True)
    event_date = models.DateField()
    incident_classification = models.CharField(max_length=10, choices=Classification.choices)
    engagement_rating = models.PositiveSmallIntegerField()
    observation_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "behavior_feedback"
        indexes = [models.Index(fields=["student", "event_date"])]
        ordering = ["-event_date"]
        constraints = [
            models.CheckConstraint(check=models.Q(engagement_rating__gte=1) & models.Q(engagement_rating__lte=5),name="chk_engagement_rating_1_5")
        ]