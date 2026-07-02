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



