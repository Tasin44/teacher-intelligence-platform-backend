from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, StudentSearchView

router = DefaultRouter()
router.register("", StudentViewSet, basename="student")

urlpatterns = [
    path("search/", StudentSearchView.as_view(), name="student-search"),
    path("", include(router.urls)),
]
