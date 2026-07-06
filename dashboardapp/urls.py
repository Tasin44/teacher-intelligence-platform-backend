from django.urls import path
from .views import (DashboardSummaryView, SubjectPerformanceView,RecentActivityView, StudentBestSubjectView)

urlpatterns = [
    path("summary", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("subject-performance", SubjectPerformanceView.as_view(), name="dashboard-subject-performance"),
    path("recent-activity", RecentActivityView.as_view(), name="dashboard-recent-activity"),
    path("best-subject", StudentBestSubjectView.as_view(), name="dashboard-best-subject"),
]
