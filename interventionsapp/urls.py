from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterventionViewSet, StudentsNeedingInterventionView

router = DefaultRouter()
router.register("", InterventionViewSet, basename="intervention")

urlpatterns = [
    path("needing-assistance/", StudentsNeedingInterventionView.as_view(), name="needing-assistance"),
    path("", include(router.urls)),
]
