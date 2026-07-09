from django.urls import path
from .views import GenerateAIRecommendationView, StudentAIRecommendationView

urlpatterns = [
    path("generate/<int:student_id>",  GenerateAIRecommendationView.as_view(), name="ai-rec-generate"),
    path("<int:student_id>",           StudentAIRecommendationView.as_view(),  name="ai-rec-get"),
]
