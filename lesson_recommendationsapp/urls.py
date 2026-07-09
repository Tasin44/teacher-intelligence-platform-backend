from django.urls import path
from .views import (
    GenerateLessonRecommendationView,
    LessonRecommendationListView,
    ApplyModificationView,
    DismissLessonRecommendationView,
    AssignmentStatusByTopicView,
)

urlpatterns = [
    path("",                                    LessonRecommendationListView.as_view(),     name="lesson-rec-list"),
    path("generate/<int:assignment_id>",        GenerateLessonRecommendationView.as_view(), name="lesson-rec-generate"),
    path("<int:rec_id>/apply",                  ApplyModificationView.as_view(),            name="lesson-rec-apply"),
    path("<int:rec_id>/dismiss",                DismissLessonRecommendationView.as_view(),  name="lesson-rec-dismiss"),
    path("assignment-status",                   AssignmentStatusByTopicView.as_view(),      name="assignment-status-by-topic"),
]
