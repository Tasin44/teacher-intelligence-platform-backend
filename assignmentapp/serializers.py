

from datetime import date
from rest_framework import serializers
from .models import Assignment, AssignmentQuestion

class AssignmentCreateSerializer(serializers.ModelSerializer):
    target_student_roll = serializers.CharField(write_only=True, required=False, allow_blank=True)
    target_group_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Assignment
        fields = ["title", "subject", "target_type", "target_student_roll", "target_group_id","ai_difficulty", "ccss_code", "due_date", "instructions", "number_of_questions"]


    def validate_number_of_questions(self, value):
        if not (1 <= value <= 50):
            raise serializers.ValidationError("number_of_questions must be between 1 and 50")
        return value

    def validate_due_date(self, value):
        if value and value < date.today():
            raise serializers.ValidationError("due_date cannot be in the past")
        return value


















