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

    def validate_score(self, value):
        if not (0 <= value <= 100):
            raise serializers.ValidationError("score must be between 0 and 100")
        return value

    def validate_assessment_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("assessment_date cannot be in the future")
        return value

    def validate_student_roll(self, value):
        from studentapp.models import Student
        teacher = self.context["request"].user
        try:
            self._student = Student.objects.get(teacher=teacher, student_roll=value)
        except Student.DoesNotExist:
            raise serializers.ValidationError("No such student for this teacher")
        return value

    def create(self, validated_data):
        validated_data.pop("student_roll")
        return AssignmentFeedback.objects.create(student=self._student, **validated_data)