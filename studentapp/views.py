from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters,status,viewsets
from rest_framework.permissions import IsAuthenticated

from coreapp.cache_utils import bump_teacher_cache_version
from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import Student
from .serializers import StudentCreateSerializer,StudentListSerializer

class StudentViewSet(StandardResponseMixin, viewsets.ModelViewSet):


    permission_classes = [IsAuthenticated,IsOwnerTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["risk_status", "student_grade", "recommended_group"]
    search_fields = ["student_name", "student_roll", "parent_name"]
    ordering_fields = ["student_name", "avg_score", "attendance_rate", "created_at"]

    def get_throttles(self):
        self.throttle_scope = "read" if self.request.method in ("GET",) else "write"
        return super().get_throttles()

    def get_queryset(self):
        # select_related avoids an extra query per row for recommended_group
        return (Student.objects
                .filter(teacher=self.request.user)
                .select_related("recommended_group"))

    def get_serializer_class(self):
        return StudentCreateSerializer if self.action in ("create", "update", "partial_update") \
            else StudentListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Could not create student",
                                        status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        student = serializer.save()
        bump_teacher_cache_version(request.user.id)
        return self.success_response(StudentListSerializer(student).data,
                                      "Student created", status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True)
        return self.success_response(self.get_paginated_response(serializer.data).data,
                                      "Students fetched")