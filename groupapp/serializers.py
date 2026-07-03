from rest_framework import serializers
from .models import Group, GroupStudent, GroupGenerationHistory


class GroupStudentMiniSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(source="student.student_id")
    student_name = serializers.CharField(source="student.student_name")
    student_roll = serializers.CharField(source="student.student_roll")



class GroupSerializer(serializers.ModelSerializer):
    students = GroupStudentMiniSerializer(source="memberships", many=True, read_only=True)#on the Group model,  group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")

    class Meta:
        model = Group
        fields = ["group_id", "group_name", "classification", "tag", "avg_score",
                  "total_students", "generated_by_ai", "generated_at", "students"]


class GroupEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["group_name", "classification", "tag"]


class GroupGenerationHistorySerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.group_name", read_only=True)

    class Meta:
        model = GroupGenerationHistory
        fields = ["generated_date", "group_name", "classification"]
















