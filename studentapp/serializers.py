from rest_framework import serializers
from .models import Student


class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["student_name", "student_roll", "student_image", "student_grade",
                  "risk_status", "reading_level", "parent_name", "parent_email"]

    def validate_student_roll(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Roll cannot be blank")
        return value

    def validate(self, attrs):
        teacher = self.context["request"].user
        roll = attrs.get("student_roll")
        qs = Student.objects.filter(teacher=teacher, student_roll=roll)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({"student_roll": "Roll already used for this teacher"})
        return attrs

    def create(self, validated_data):
        validated_data["teacher"] = self.context["request"].user
        return super().create(validated_data)