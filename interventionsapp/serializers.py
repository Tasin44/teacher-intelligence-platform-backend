from rest_framework import serializers
from .models import Intervention


class InterventionSerializer(serializers.ModelSerializer):
    # write-only resolution fields
    student_roll = serializers.CharField(write_only=True, required=False, allow_blank=True)
    group_id     = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    # read-only display fields
    student_name = serializers.CharField(source="student.student_name", read_only=True, default=None)
    student_roll_out = serializers.CharField(source="student.student_roll", read_only=True, default=None)
    group_name   = serializers.CharField(source="group.group_name",   read_only=True, default=None)

    class Meta:
        model  = Intervention
        fields = [
            "intervention_id", "target_type",
            # write
            "student_roll", "group_id",
            # read
            "student_name", "student_roll_out", "group_name",
            # common
            "intervention_type", "reason", "start_date", "frequency", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["intervention_id", "created_at", "updated_at"]