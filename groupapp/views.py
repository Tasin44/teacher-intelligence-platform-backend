from django.shortcuts import render

# Create your views here.

from django.db import transaction
from django.db.models import Avg, Count, Max
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.cache_utils import bump_teacher_cache_version
from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from dashboardapp.models import ActivityLog
from .models import Group, GroupGenerationHistory
from .serializers import GroupSerializer, GroupEditSerializer, GroupGenerationHistorySerializer
from .grouping_service import generate_groups



class GenerateGroupsView(StandardResponseMixin, APIView):
    """POST /api/groups/generate -> (re)runs the AI grouping algorithm for this teacher"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "ai_generate"

    @transaction.atomic
    def post(self, request):
        groups = generate_groups(request.user)
        if not groups:
            return self.error_response("No students found to group", status.HTTP_400_BAD_REQUEST)
        ActivityLog.objects.create(
            teacher=request.user, activity_type="group_generated",
            description=f"AI generated {len(groups)} group(s) from current performance data")
        bump_teacher_cache_version(request.user.id)
        return self.success_response(GroupSerializer(groups, many=True).data,
                                      "Groups generated", status.HTTP_201_CREATED) 