from django.shortcuts import render

# Create your views here.
from calendar import monthrange
from datetime import date

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.cache_utils import bump_teacher_cache_version
from coreapp.response import StandardResponseMixin
from .models import Attendance, OffDay
from .serializers import AttendanceSerializer, OffDaySerializer


class OffDayView(StandardResponseMixin, APIView):
    """POST /api/attendance/off-day"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "write"

    def post(self, request):
        serializer = OffDaySerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Could not create off day",status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        off_day = serializer.save()
        bump_teacher_cache_version(request.user.id)
        return self.success_response(OffDaySerializer(off_day).data, "Off day created",status.HTTP_201_CREATED)



class AttendanceView(StandardResponseMixin, APIView):
    """
    POST /api/attendance   -> mark present/absent/late for a student+date (idempotent upsert)
    Response includes that student's attendance rate for the month of attendance_date.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope = "write"

    def post(self, request):
        serializer = AttendanceSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Could not mark attendance",status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        record = serializer.save()
        bump_teacher_cache_version(request.user.id)

        d = record.attendance_date
        start = d.replace(day=1)
        end = d.replace(day=monthrange(d.year, d.month)[1])
        month_qs = Attendance.objects.filter(student=record.student,attendance_date__range=(start, end))
        total = month_qs.count()
        present_or_late = month_qs.filter(status__in=["present", "late"]).count()
        monthly_rate = round((present_or_late / total) * 100, 2) if total else None

        return self.success_response({
            "attendance_id": record.attendance_id,
            "student_id": record.student_id,
            "attendance_date": record.attendance_date,
            "status": record.status,
            "monthly_attendance_rate": monthly_rate,
        }, "Attendance recorded", status.HTTP_201_CREATED)



class StudentMonthlyAttendanceView(StandardResponseMixin, APIView):
    """GET /api/attendance/student/{student_id}/monthly?year=2026&month=6"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"


    def get(self, request, student_id):
        from studentapp.models import Student
        try:
            student = Student.objects.get(pk=student_id, teacher=request.user)
        except Student.DoesNotExist:
            return self.error_response("Student not found", status.HTTP_404_NOT_FOUND)

        today = date.today()
        year = int(request.query_params.get("year", today.year))
        month = int(request.query_params.get("month", today.month))
        if not (1 <= month <= 12):
            return self.error_response("month must be between 1 and 12", status.HTTP_400_BAD_REQUEST)

        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        records = Attendance.objects.filter(student=student, attendance_date__range=(start, end))
        total = records.count()
        present_or_late = records.filter(status__in=["present", "late"]).count()
        rate = round((present_or_late / total) * 100, 2) if total else None

        return self.success_response({
            "student_id": student.student_id,
            "year": year,
            "month": month,
            "attendance_rate": rate,
            "days": [{"date": r.attendance_date, "status": r.status} for r in records.order_by("attendance_date")],
        }, "Monthly attendance fetched")









