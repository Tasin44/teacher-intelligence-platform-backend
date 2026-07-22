import ast
import json

from rest_framework import serializers
from .models import LessonRecommendation


class LessonRecommendationSerializer(serializers.ModelSerializer):
    assignment_title     = serializers.CharField(source="assignment.title",             read_only=True)
    applied_student_name = serializers.CharField(source="applied_student.student_name", read_only=True, default=None)
    applied_group_name   = serializers.CharField(source="applied_group.group_name",     read_only=True, default=None)

    # applied_demographics: human-readable string e.g. "group: Group A" / "student: John"
    applied_demographics    = serializers.SerializerMethodField()
    # Override recommendation_details to always serve valid JSON string
    recommendation_details  = serializers.SerializerMethodField()

    class Meta:
        model  = LessonRecommendation
        fields = [
            "lesson_rec_id", "assignment_title", "recommendation_date",
            "recommendation_details", "applied_demographics",
            "applied_student_name", "applied_group_name",
            "status",
        ]

    def get_recommendation_details(self, obj):
        """
        Normalise whatever is stored in the DB into a proper JSON string with
        strugglingStudents / advancedStudents keys so the frontend can always
        do JSON.parse() safely.
        """
        raw = obj.recommendation_details or ""

        # 1. Already valid JSON?
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and (
                "strugglingStudents" in data or "advancedStudents" in data
            ):
                return json.dumps(data, ensure_ascii=False)
            # Wrapped under "recommendation" key (old format)
            if isinstance(data, dict) and "recommendation" in data:
                inner = data["recommendation"]
                if isinstance(inner, dict):
                    return json.dumps(inner, ensure_ascii=False)
                return json.dumps({"strugglingStudents": [str(inner)], "advancedStudents": []})
        except (ValueError, TypeError):
            pass

        # 2. Try Python literal_eval (handles single-quoted Python repr dicts)
        try:
            data = ast.literal_eval(raw)
            if isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False)
        except Exception:
            pass

        # 3. Last resort: wrap as single struggling tip
        return json.dumps({"strugglingStudents": [raw], "advancedStudents": []})

    def get_applied_demographics(self, obj):
        if obj.applied_target_type == "student" and obj.applied_student:
            return f"student: {obj.applied_student.student_name}"
        if obj.applied_target_type == "group" and obj.applied_group:
            return f"group: {obj.applied_group.group_name}"
        return None

class ApplyModificationSerializer(serializers.Serializer):
    """Used when teacher clicks 'Apply Modification'."""
    applied_target_type = serializers.ChoiceField(choices=["student", "group"])
    applied_student_id  = serializers.IntegerField(required=False, allow_null=True)
    applied_group_id    = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        # Both IDs are optional — class-level application is allowed without a specific target
        return attrs