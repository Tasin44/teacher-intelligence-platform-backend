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



class GroupViewSet(StandardResponseMixin, viewsets.ModelViewSet):



    permission_classes = [IsAuthenticated, IsOwnerTeacher]
    http_method_names = ["get", "patch", "head", "options"]


    def get_throttles(self):
        self.throttle_scope = "read" if self.request.method == "GET" else "write"
        return super().get_throttles()

    def get_queryset(self):
        return Group.objects.filter(teacher=self.request.user).prefetch_related("memberships__student")


    def get_serializer_class(self):
        return GroupEditSerializer if self.action == "partial_update" else GroupSerializer

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        serializer = GroupSerializer(page, many=True)
        return self.success_response(self.get_paginated_response(serializer.data).data,"Groups fetched")


    def retrieve(self, request, *args, **kwargs):
        return self.success_response(GroupSerializer(self.get_object()).data, "Group fetched")


    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = GroupEditSerializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.error_response("Update failed", status.HTTP_422_UNPROCESSABLE_ENTITY,
                                        serializer.errors)
        group = serializer.save()
        bump_teacher_cache_version(request.user.id)
        return self.success_response(GroupSerializer(group).data, "Group updated")




