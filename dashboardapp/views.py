


from django.core.cache import cache
from django.db.models import Avg, Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.cache_utils import CACHE_TTL_DASHBOARD, scoped_cache_key
from coreapp.response import StandardResponseMixin
from studentapp.models import Student
from feedbackapp.models import AssignmentFeedback
from .models import ActivityLog



class DashboardSummaryView(StandardResponseMixin, APIView):
    """
    GET /api/dashboard/summary
    -> total / risk / on_track / advance / developing student counts.
    Cached per-teacher; invalidated automatically whenever a student row changes
    (bump_teacher_cache_version is called from the students app on write).
    """
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"

    def get(self, request):
        cache_key = scoped_cache_key(request.user.id, "dashboard_summary")
        data = cache.get(cache_key)
        if data is None:
            counts = (Student.objects.filter(teacher=request.user).values("risk_status").annotate(c=Count("student_id")))
            bucket = {row["risk_status"]: row["c"] for row in counts}
            data = {
                "total_students": sum(bucket.values()),
                "risk_students": bucket.get("at_risk", 0),
                "on_track_students": bucket.get("on_track", 0),
                "advance_students": bucket.get("advance", 0),
                "developing_students": bucket.get("developing", 0),
            }
            cache.set(cache_key, data, timeout=CACHE_TTL_DASHBOARD)
        return self.success_response(data, "Dashboard summary fetched")


class SubjectPerformanceView(StandardResponseMixin, APIView):
    """GET /api/dashboard/subject-performance -> bar-graph data: avg score per subject"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"

    def get(self, request):
        cache_key = scoped_cache_key(request.user.id, "subject_performance")
        data = cache.get(cache_key)
        if data is None:
            rows = (AssignmentFeedback.objects
                    .filter(student__teacher=request.user)
                    .values("subject")
                    .annotate(avg_score=Avg("score"))
                    .order_by("subject"))
            data = [{"subject": r["subject"], "avg_score": round(r["avg_score"], 2)} for r in rows]
            cache.set(cache_key, data, timeout=CACHE_TTL_DASHBOARD)
        return self.success_response(data, "Subject performance fetched")


class RecentActivityView(StandardResponseMixin, APIView):
    """GET /api/dashboard/recent-activity?limit=20"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 20)), 100)
        rows = (ActivityLog.objects.filter(teacher=request.user)
                .order_by("-created_at")[:limit])
        data = [{"activity_type": r.activity_type, "description": r.description,
                 "created_at": r.created_at} for r in rows]
        return self.success_response(data, "Recent activity fetched")




