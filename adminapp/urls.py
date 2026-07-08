from django.urls import path
from .views import (
    AdminLoginView, AdminDashboardStatsView, AdminPlatformUsageView,
    AdminTeacherViewSet, AdminTeacherActivityView, AdminSchoolViewSet,
    AdminAnalysisReportView, AdminAIConfigView, AdminAllTeachersActivityView,
    AdminTeacherApproveView
)

urlpatterns = [
    path("login", AdminLoginView.as_view(), name="admin-login"),
    path("dashboard-stats", AdminDashboardStatsView.as_view(), name="admin-dashboard-stats"),
    path("platform-usage", AdminPlatformUsageView.as_view(), name="admin-platform-usage"),
    
    path("teachers", AdminTeacherViewSet.as_view({'get': 'list', 'post': 'create'}), name="admin-teachers"),
    path("teachers/activity", AdminAllTeachersActivityView.as_view(), name="admin-all-teachers-activity"),
    path("teachers/<int:pk>/activity", AdminTeacherActivityView.as_view(), name="admin-teacher-activity"),
    path("teachers/<int:pk>/approve", AdminTeacherApproveView.as_view(), name="admin-teacher-approve"),
    
    path("schools", AdminSchoolViewSet.as_view({'get': 'list', 'post': 'create'}), name="admin-schools"),
    path("schools/<int:pk>/", AdminSchoolViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name="admin-school-detail"),
    
    path("analysis-report", AdminAnalysisReportView.as_view(), name="admin-analysis-report"),
    path("ai-config", AdminAIConfigView.as_view(), name="admin-ai-config"),
]
