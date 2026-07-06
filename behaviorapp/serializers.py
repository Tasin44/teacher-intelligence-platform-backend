from datetime import date
from rest_framework import serializers
from .models import BehaviorFeedback


class BehaviorFeedbackSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(write_only=True)

    class Meta:
        model = BehaviorFeedback
        fields = ["behavior_id", "student_roll", "event_date", "incident_classification",
                  "engagement_rating", "observation_note"]