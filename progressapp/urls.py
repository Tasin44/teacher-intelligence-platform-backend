from django.urls import path
from .views import (
    StudentOverallGrowthView,
    StudentMonthlyAttendanceTrendView,
    StudentWeeklyScoreView,
    ClassAttendanceRateView,
)

urlpatterns = [
    path("student/<int:student_id>/overall",         StudentOverallGrowthView.as_view(),          name="progress-overall"),
    path("student/<int:student_id>/attendance",      StudentMonthlyAttendanceTrendView.as_view(), name="progress-monthly-attendance"),
    path("student/<int:student_id>/scores-weekly",   StudentWeeklyScoreView.as_view(),            name="progress-weekly-scores"),
    path("class-attendance",                          ClassAttendanceRateView.as_view(),           name="progress-class-attendance"),
]
