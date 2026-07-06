

from datetime import date
from rest_framework import serializers
from .models import Assignment, AssignmentQuestion

class AssignmentCreateSerializer(serializers.ModelSerializer):
    target_student_roll = serializers.CharField(write_only=True, required=False, allow_blank=True)
    target_group_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)























