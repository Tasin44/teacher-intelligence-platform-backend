from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GenerateGroupsView, GroupViewSet, GroupStatsView, GroupGenerationHistoryView, GroupGenerateHistorySummaryView, GroupAllView


router = DefaultRouter()


router.register("", GroupViewSet, basename="group")

urlpatterns = [
    path("all", GroupAllView.as_view(), name="group-all"),
    path("generate/history", GroupGenerateHistorySummaryView.as_view(), name="group-generate-history"),
    path("generate", GenerateGroupsView.as_view(), name="group-generate"),
    path("stats", GroupStatsView.as_view(), name="group-stats"),
    path("history", GroupGenerationHistoryView.as_view(), name="group-history"),
] + router.urls
