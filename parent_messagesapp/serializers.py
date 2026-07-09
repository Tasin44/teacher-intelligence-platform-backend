from rest_framework import serializers
from .models import AIParentMessage


class GenerateMessageSerializer(serializers.Serializer):
    """Input for generating a parent message."""
    student_roll   = serializers.CharField()
    classification = serializers.ChoiceField(choices=AIParentMessage.Classification.choices)
    tone           = serializers.ChoiceField(choices=AIParentMessage.Tone.choices)

    def validate_student_roll(self, value):
        from studentapp.models import Student
        teacher = self.context["request"].user
        try:
            self._student = Student.objects.get(teacher=teacher, student_roll=value)
        except Student.DoesNotExist:
            raise serializers.ValidationError("No such student for this teacher")
        if not self._student.parent_email:
            raise serializers.ValidationError("This student has no parent email on record")
        return value