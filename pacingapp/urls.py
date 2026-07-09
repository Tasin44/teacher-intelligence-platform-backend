from django.urls import path
from .views import GeneratePacingView, PacingListView

urlpatterns = [
    path("",                              PacingListView.as_view(),     name="pacing-list"),
    path("generate/<int:assignment_id>",  GeneratePacingView.as_view(), name="pacing-generate"),
]
