from rest_framework import serializers
from .models import School, AIConfiguration
from authapp.models import Teacher


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["school_id", "school_name", "region_district_office", "registration_status", "created_at"]


class SchoolStatsSerializer(serializers.ModelSerializer):
    total_teachers = serializers.IntegerField(read_only=True)
    total_students = serializers.IntegerField(read_only=True)
    total_ai_requests = serializers.IntegerField(read_only=True)

    class Meta:
        model = School
        fields = ["school_id", "school_name", "region_district_office", "registration_status", 
                  "total_teachers", "total_students", "total_ai_requests"]


class AdminTeacherSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = ["teacher_id", "first_name", "last_name", "email", 
                  "school_name", "grade", "room", "approval_status", "is_active", "created_at"]


class AdminTeacherCreateSerializer(serializers.ModelSerializer):
    school_id = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), source="school")
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Teacher
        fields = ["first_name", "last_name", "email", "password", 
                  "school_id", "grade", "room", "approval_status"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        teacher = Teacher(**validated_data)
        teacher.set_password(password)
        teacher.is_verified = True # Admin creates verified accounts
        teacher.save()
        return teacher


class AIConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConfiguration
        fields = ["temperature", "max_tokens", "ai_model", "updated_at"]


class AnalysisReportRequestSerializer(serializers.Serializer):
    analyticalFocus = serializers.CharField(max_length=255)
    targetSchoolRange = serializers.PrimaryKeyRelatedField(queryset=School.objects.all())
    temporalBounds = serializers.IntegerField(help_text="Last how many days", min_value=1)
