from rest_framework import serializers
from .models import LessonRecommendation


class LessonRecommendationSerializer(serializers.ModelSerializer):
    assignment_title     = serializers.CharField(source="assignment.title",             read_only=True)
    applied_student_name = serializers.CharField(source="applied_student.student_name", read_only=True, default=None)
    applied_group_name   = serializers.CharField(source="applied_group.group_name",     read_only=True, default=None)

    # applied_demographics: human-readable string e.g. "group: Group A" / "student: John"
    applied_demographics = serializers.SerializerMethodField()

    class Meta:
        model  = LessonRecommendation
        fields = [
            "lesson_rec_id", "assignment_title", "recommendation_date",
            "recommendation_details", "applied_demographics",
            "applied_student_name", "applied_group_name",
            "status",
        ]

    def get_applied_demographics(self, obj):
        if obj.applied_target_type == "student" and obj.applied_student:
            return f"student: {obj.applied_student.student_name}"
        if obj.applied_target_type == "group" and obj.applied_group:
            return f"group: {obj.applied_group.group_name}"
        return None
