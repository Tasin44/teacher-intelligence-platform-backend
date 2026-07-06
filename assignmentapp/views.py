from django.shortcuts import render

# Create your views here.
from django.core.cache import cache
from django.db import transaction 
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters,status,viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


from coreapp.cache_utils import (CACHE_TTL_LISTS, bump_teacher_cache_version,binary_search_title_prefix, scoped_cache_key)
from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import Assignment, AssignmentQuestion, AssignmentMailLog


def _resolve_target_students(assignment: Assignment):
    """Flatten target_type into a concrete list of Student rows to notify."""
    from studentapp.models import Student
    if assignment.target_type == Assignment.TargetType.STUDENT and assignment.target_student:
        return [assignment.target_student]
    if assignment.target_type == Assignment.TargetType.GROUP and assignment.target_group:
        return list(Student.objects.filter(
            group_memberships__group=assignment.target_group))
    if assignment.target_type == Assignment.TargetType.ALL_GROUPS:
        return list(Student.objects.filter(teacher=assignment.teacher))
    return []

def _log_activity(teacher_id, activity_type, description, reference_id=None):
    from dashboardapp.models import ActivityLog
    ActivityLog.objects.create(teacher_id=teacher_id, activity_type=activity_type,description=description, reference_id=reference_id)





class AssignmentViewSet(StandardResponseMixin, viewsets.ModelViewSet):


    permission_classes = [IsAuthenticated, IsOwnerTeacher]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["subject", "tag", "target_type", "ai_generation_status"]
    ordering_fields = ["due_date", "creation_date", "title"]












