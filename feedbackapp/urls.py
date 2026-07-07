from rest_framework.routers import DefaultRouter
from .views import AssignmentFeedbackViewSet

router = DefaultRouter()
router.register("", AssignmentFeedbackViewSet, basename="assignment-feedback")

urlpatterns = router.urls
