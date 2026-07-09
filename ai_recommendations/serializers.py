from rest_framework import serializers
from .models import AIRecommendation


class AIRecommendationSerializer(serializers.ModelSerializer):
    student_name    = serializers.CharField(source="student.student_name",  read_only=True)
    reading_level   = serializers.CharField(source="student.reading_level", read_only=True)
    avg_score       = serializers.DecimalField(source="student.avg_score",max_digits=5, decimal_places=2, read_only=True)
    attendance_rate = serializers.DecimalField(source="student.attendance_rate",max_digits=5, decimal_places=2, read_only=True)
    recommended_group = serializers.CharField(source="student.recommended_group.group_name",read_only=True, default=None)

    class Meta:
        model  = AIRecommendation
        fields = [
            "recommendation_id", "student_name", "reading_level",
            "avg_score", "attendance_rate", "recommended_group",
            "current_strengths", "recommended_activities", "skill_gaps",
            "generated_at",
        ]
