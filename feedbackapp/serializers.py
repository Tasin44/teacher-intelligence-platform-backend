from datetime import date
from rest_framework import serializers
from .models import AssignmentFeedback



class AssignmentFeedbackSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(write_only=True)

    class Meta:
        model = AssignmentFeedback
        fields = ["feedback_id", "student_roll", "subject", "title", "score",
                  "ccss_code", "assessment_date", "status"]
        read_only_fields = ["feedback_id"]

