from authapp.urls import urlpatterns
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GenerateGroupsView,GroupViewSet,GroupStatsView,GroupGenerationHistoryView


router=DefaultRouter()


router.register("",GroupViewSet,basename="group")

urlpatterns = [
    path("generate", GenerateGroupsView.as_view(), name="group-generate"),
    path("stats", GroupStatsView.as_view(), name="group-stats"),
    path("history", GroupGenerationHistoryView.as_view(), name="group-history"),
] + router.urls










