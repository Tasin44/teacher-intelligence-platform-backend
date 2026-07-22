from django.core.cache import cache
from django.db import transaction
from django.db.models import Max, Count
from django.db.models.functions import TruncDate
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.cache_utils import bump_teacher_cache_version, scoped_cache_key, CACHE_TTL_DASHBOARD
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
        bump_teacher_cache_version(request.user.pk)
        return self.success_response(GroupSerializer(groups, many=True).data,
                                      "Groups generated", status.HTTP_201_CREATED)



class GroupViewSet(StandardResponseMixin, viewsets.ModelViewSet):

    """
    GET   /api/groups               -> list generated groups
    GET   /api/groups/{id}
    PATCH /api/groups/{id}          -> edit name/tag/classification
    """

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
        return self.success_response(self.get_paginated_response(serializer.data).data, "Groups fetched")


    def retrieve(self, request, *args, **kwargs):
        return self.success_response(GroupSerializer(self.get_object()).data, "Group fetched")


    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = GroupEditSerializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.error_response("Update failed", status.HTTP_422_UNPROCESSABLE_ENTITY,
                                        serializer.errors)
        group = serializer.save()
        bump_teacher_cache_version(request.user.pk)
        return self.success_response(GroupSerializer(group).data, "Group updated")



class GroupStatsView(StandardResponseMixin, APIView):
    """GET /api/groups/stats -> total students, total groups, avg group size, last formed date"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"

    def get(self, request):
        cache_key = scoped_cache_key(request.user.pk, "group_stats")
        data = cache.get(cache_key)
        if data is None:
            groups = Group.objects.filter(teacher=request.user)
            last_formed = groups.aggregate(last_formed=Max("generated_at"))["last_formed"]
            total_groups = groups.count()
            total_students = sum(groups.values_list("total_students", flat=True))
            avg_size = round(total_students / total_groups, 2) if total_groups else 0
            data = {
                "total_students": total_students,
                "total_groups": total_groups,
                "avg_group_size": avg_size,
                "last_group_formed": last_formed,
            }
            cache.set(cache_key, data, timeout=CACHE_TTL_DASHBOARD)
        return self.success_response(data, "Group stats fetched")


class GroupGenerationHistoryView(StandardResponseMixin, APIView):
    """GET /api/groups/history"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"

    def get(self, request):
        cache_key = scoped_cache_key(request.user.pk, "group_gen_history")
        data = cache.get(cache_key)
        if data is None:
            rows = (GroupGenerationHistory.objects.filter(teacher=request.user)
                    .select_related("group").order_by("-generated_date")[:200])
            data = GroupGenerationHistorySerializer(rows, many=True).data
            cache.set(cache_key, data, timeout=CACHE_TTL_DASHBOARD)
        return self.success_response(data, "Generation history fetched")

class GroupGenerateHistorySummaryView(StandardResponseMixin, APIView):
    """GET /api/groups/generate/history"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"

    def get(self, request):
        cache_key = scoped_cache_key(request.user.pk, "group_gen_summary")
        data = cache.get(cache_key)
        if data is None:
            qs = (GroupGenerationHistory.objects.filter(teacher=request.user)
                  .annotate(date=TruncDate("generated_date"))
                  .values("date")
                  .annotate(groups_formed=Count("id"))
                  .order_by("-date"))
            
            data = [
                {
                    "date": item["date"],
                    "groups_formed": item["groups_formed"]
                }
                for item in qs
            ]
            cache.set(cache_key, data, timeout=CACHE_TTL_DASHBOARD)
        return self.success_response(data, "Generation history summary fetched")
