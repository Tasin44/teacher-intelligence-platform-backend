from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, StudentSearchView, StudentDiagnosticView

router = DefaultRouter()
router.register("", StudentViewSet, basename="student")

urlpatterns = [
    path("search/", StudentSearchView.as_view(), name="student-search"),
    path("<int:student_id>/diagnostic/", StudentDiagnosticView.as_view(), name="student-diagnostic"),
    path("", include(router.urls)),
]
