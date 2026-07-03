from rest_framework import serializers
from .models import Group, GroupStudent, GroupGenerationHistory


class GroupStudentMiniSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(source="student.student_id")
    student_name = serializers.CharField(source="student.student_name")
    student_roll = serializers.CharField(source="student.student_roll")




















