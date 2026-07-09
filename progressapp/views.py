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


class StudentMonthlyAttendanceTrendView(StandardResponseMixin, APIView):
    """
    GET /api/progress/student/{student_id}/attendance?months=6
    Returns monthly attendance rate for the last N months.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request, student_id):
        try:
            Student.objects.get(pk=student_id, teacher=request.user)
        except Student.DoesNotExist:
            return self.error_response("Student not found", 404)

        months = min(int(request.query_params.get("months", 6)), 24)
        today  = date.today()
        result = []

        for i in range(months - 1, -1, -1):
            # go back i months
            month = (today.month - i - 1) % 12 + 1
            year  = today.year - ((today.month - i - 1) // 12)
            start = date(year, month, 1)
            end   = date(year, month, monthrange(year, month)[1])

            qs    = Attendance.objects.filter(student_id=student_id, attendance_date__range=(start, end))
            total = qs.count()
            present_or_late = qs.filter(status__in=["present", "late"]).count()
            rate  = round((present_or_late / total) * 100, 2) if total else None

            result.append({"year": year, "month": month, "attendance_rate": rate, "total_days": total})

        return self.success_response(result, "Monthly attendance trend fetched")


class StudentWeeklyScoreView(StandardResponseMixin, APIView):
    """
    GET /api/progress/student/{student_id}/scores-weekly?weeks=8
    Returns average assignment score per week for the last N weeks.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request, student_id):
        try:
            Student.objects.get(pk=student_id, teacher=request.user)
        except Student.DoesNotExist:
            return self.error_response("Student not found", 404)

        weeks = min(int(request.query_params.get("weeks", 8)), 52)
        today = date.today()
        result = []

        for i in range(weeks - 1, -1, -1):
            week_end   = today - timedelta(days=today.weekday() + 7 * i)
            week_start = week_end - timedelta(days=6)
            qs  = AssignmentFeedback.objects.filter(
                student_id=student_id,
                assessment_date__range=(week_start, week_end))
            agg = qs.aggregate(avg=Avg("score"), count=Count("feedback_id"))
            result.append({
                "week_start": week_start,
                "week_end":   week_end,
                "avg_score":  round(agg["avg"], 2) if agg["avg"] else None,
                "count":      agg["count"],
            })

        return self.success_response(result, "Weekly score trend fetched")

class ClassAttendanceRateView(StandardResponseMixin, APIView):
    """
    GET /api/progress/class-attendance
    Overall attendance rate across all students for this teacher.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request):
        student_ids = Student.objects.filter(teacher=request.user).values_list("student_id", flat=True)
        qs          = Attendance.objects.filter(student_id__in=student_ids)
        total       = qs.count()
        present     = qs.filter(status__in=["present", "late"]).count()
        rate        = round((present / total) * 100, 2) if total else None
        return self.success_response({"class_attendance_rate": rate, "total_days_recorded": total},"Class attendance rate fetched")

