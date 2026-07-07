from rest_framework.routers import DefaultRouter
from .views import BehaviorFeedbackViewSet

router = DefaultRouter()
router.register("", BehaviorFeedbackViewSet, basename="behavior-feedback")

urlpatterns = router.urls
