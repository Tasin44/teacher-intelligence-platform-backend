from django.urls import path
from .views import OffDayView, AttendanceView, StudentMonthlyAttendanceView

urlpatterns = [
    path("off-day", OffDayView.as_view(), name="attendance-off-day"),
    path("mark", AttendanceView.as_view(), name="attendance-mark"),
    path(
        "student/<int:student_id>/monthly",
        StudentMonthlyAttendanceView.as_view(),
        name="attendance-student-monthly",
    ),
]
