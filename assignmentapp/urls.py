from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AssignmentViewSet, PublicAssignmentSubmissionView

router = DefaultRouter()
router.register("", AssignmentViewSet, basename="assignment")

urlpatterns = [
    path("public/<str:unique_code>/submit", PublicAssignmentSubmissionView.as_view(), name="assignment-public-submit"),
] + router.urls
