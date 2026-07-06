from datetime import date
from rest_framework import serializers
from .models import BehaviorFeedback


class BehaviorFeedbackSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(write_only=True)

    class Meta:
        model = BehaviorFeedback
        fields = ["behavior_id", "student_roll", "event_date", "incident_classification","engagement_rating", "observation_note"]

    def validate_engagement_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("engagement_rating must be between 1 and 5")
        return value

    def validate_event_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("event_date cannot be in the future")
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
        return BehaviorFeedback.objects.create(student=self._student, **validated_data)