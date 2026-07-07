from datetime import date
from rest_framework import serializers
from .models import Observation


class ObservationSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(write_only=True)

    class Meta:
        model = Observation
        fields = ["observation_id", "student_roll", "observation_date", "setting_tag", "notes"]


    def validate_observation_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("observation_date cannot be in the future")
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
        return Observation.objects.create(student=self._student, **validated_data)


        