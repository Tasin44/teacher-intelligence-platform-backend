from rest_framework.routers import DefaultRouter
from .views import ObservationViewSet

router = DefaultRouter()
router.register("", ObservationViewSet, basename="observation")

urlpatterns = router.urls
