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

    def validate(self, attrs):
        target_type  = attrs.get("target_type", getattr(self.instance, "target_type", None))
        student_roll = attrs.get("student_roll", "")
        group_id     = attrs.get("group_id")
        teacher      = self.context["request"].user

        if target_type == Intervention.TargetType.STUDENT:
            if not student_roll:
                raise serializers.ValidationError(
                    {"student_roll": "Required when target_type is individual_student"})
            from studentapp.models import Student
            try:
                attrs["_student"] = Student.objects.get(teacher=teacher, student_roll=student_roll)
            except Student.DoesNotExist:
                raise serializers.ValidationError({"student_roll": "No such student for this teacher"})

        elif target_type == Intervention.TargetType.GROUP:
            if not group_id:
                raise serializers.ValidationError(
                    {"group_id": "Required when target_type is individual_group"})
            from groupapp.models import Group
            try:
                attrs["_group"] = Group.objects.get(teacher=teacher, pk=group_id)
            except Group.DoesNotExist:
                raise serializers.ValidationError({"group_id": "No such group for this teacher"})

        return attrs

    def create(self, validated_data):
        validated_data.pop("student_roll", None)
        validated_data.pop("group_id", None)
        student = validated_data.pop("_student", None)
        group   = validated_data.pop("_group",   None)
        return Intervention.objects.create(
            teacher=self.context["request"].user,
            student=student,
            group=group,
            **validated_data,
        )

    def update(self, instance, validated_data):
        validated_data.pop("student_roll", None)
        validated_data.pop("group_id", None)
        validated_data.pop("_student", None)
        validated_data.pop("_group", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

