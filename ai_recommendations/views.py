from django.shortcuts import render

# Create your views here.
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.response import StandardResponseMixin
from studentapp.models import Student
from .models import AIRecommendation
from .serializers import AIRecommendationSerializer
from .services import AIRecommendationError, generate_ai_recommendation


class GenerateAIRecommendationView(StandardResponseMixin, APIView):
    """
    POST /api/ai-recommendations/generate/{student_id}
    Calls OpenAI with all student data → saves + returns recommendation.
    Result is cached for 30 min (re-POST regenerates and busts cache).
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "ai_generate"

    def post(self, request, student_id):
        try:
            student = Student.objects.select_related("recommended_group").get(
                pk=student_id, teacher=request.user)
        except Student.DoesNotExist:
            return self.error_response("Student not found", status.HTTP_404_NOT_FOUND)

        try:
            result = generate_ai_recommendation(student)
        except AIRecommendationError as exc:
            return self.error_response(f"AI generation failed: {exc}", status.HTTP_502_BAD_GATEWAY)

        rec = AIRecommendation.objects.create(student=student, **result)
        cache.set(f"ai_rec:{student_id}", rec.recommendation_id, timeout=1800)

        return self.success_response(
            AIRecommendationSerializer(rec).data,
            "AI recommendation generated", status.HTTP_201_CREATED)

class StudentAIRecommendationView(StandardResponseMixin, APIView):
    """
    GET /api/ai-recommendations/{student_id}
    Returns the latest recommendation for a student (from cache if available).
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request, student_id):
        try:
            Student.objects.get(pk=student_id, teacher=request.user)
        except Student.DoesNotExist:
            return self.error_response("Student not found", status.HTTP_404_NOT_FOUND)

        rec = (AIRecommendation.objects
               .filter(student_id=student_id)
               .select_related("student__recommended_group")
               .first())
        if not rec:
            return self.error_response(
                "No recommendation generated yet. POST to /generate/ first.",
                status.HTTP_404_NOT_FOUND)

        return self.success_response(AIRecommendationSerializer(rec).data,"AI recommendation fetched")
