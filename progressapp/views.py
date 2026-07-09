from django.shortcuts import render

# Create your views here.
from calendar import monthrange
from datetime import date, timedelta

from django.db.models import Avg, Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.response import StandardResponseMixin
from studentapp.models import Student
from feedbackapp.models import AssignmentFeedback
from attendenceapp.models import Attendance


class StudentOverallGrowthView(StandardResponseMixin, APIView):
    """
    GET /api/progress/student/{student_id}/overall
    Returns overall growth metrics: avg_score, attendance_rate,
    risk_status, reading_level, recommended_group.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request, student_id):
        try:
            student = Student.objects.select_related("recommended_group").get(
                pk=student_id, teacher=request.user)
        except Student.DoesNotExist:
            return self.error_response("Student not found", 404)

        # subject-level breakdown for richer growth view
        subject_breakdown = list(
            AssignmentFeedback.objects.filter(student=student)
            .values("subject").annotate(avg_score=Avg("score")).order_by("subject")
        )

        return self.success_response({
            "student_id":        student.student_id,
            "student_name":      student.student_name,
            "risk_status":       student.risk_status,
            "reading_level":     student.reading_level,
            "avg_score":         student.avg_score,
            "attendance_rate":   student.attendance_rate,
            "recommended_group": student.recommended_group.group_name if student.recommended_group else None,
            "subject_breakdown": [
                {"subject": r["subject"], "avg_score": round(r["avg_score"], 2)}
                for r in subject_breakdown
            ],
        }, "Overall growth fetched")