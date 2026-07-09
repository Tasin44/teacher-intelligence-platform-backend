from rest_framework import serializers
from .models import PacingRecommendation


class PacingRecommendationSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source="assignment.title", read_only=True, default=None)

    class Meta:
        model  = PacingRecommendation
        fields = [
            "pacing_id", "topic", "assignment_title",
            "curriculum_adjustment", "standards_coverage_checklist",
            "generated_at",
        ]
