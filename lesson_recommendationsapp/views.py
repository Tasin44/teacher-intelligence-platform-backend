from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.response import StandardResponseMixin
from assignmentapp.models import Assignment
from .models import LessonRecommendation
from .serializers import LessonRecommendationSerializer, ApplyModificationSerializer
from .services import LessonRecommendationError, generate_lesson_recommendation


class GenerateLessonRecommendationView(StandardResponseMixin, APIView):
    """
    POST /api/lesson-recommendations/generate/{assignment_id}
    AI analyses the assignment scores → saves a LessonRecommendation row.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "ai_generate"

    def post(self, request, assignment_id):
        try:
            assignment = Assignment.objects.get(pk=assignment_id, teacher=request.user)
        except Assignment.DoesNotExist:
            return self.error_response("Assignment not found", status.HTTP_404_NOT_FOUND)

        try:
            details = generate_lesson_recommendation(assignment)
        except LessonRecommendationError as exc:
            return self.error_response(f"AI generation failed: {exc}", status.HTTP_502_BAD_GATEWAY)

        rec = LessonRecommendation.objects.create(
            assignment=assignment,
            recommendation_details=details,
        )
        return self.success_response(
            LessonRecommendationSerializer(rec).data,
            "Lesson recommendation generated", status.HTTP_201_CREATED)


class LessonRecommendationListView(StandardResponseMixin, APIView):
    """
    GET /api/lesson-recommendations/
    ?assignment_id=  filter by assignment
    ?status=applied|pending|dismiss
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request):
        qs = (LessonRecommendation.objects
              .filter(assignment__teacher=request.user)
              .select_related("assignment", "applied_student", "applied_group"))
        if aid := request.query_params.get("assignment_id"):
            qs = qs.filter(assignment_id=aid)
        if s := request.query_params.get("status"):
            qs = qs.filter(status=s)
        return self.success_response(
            LessonRecommendationSerializer(qs, many=True).data,
            "Lesson recommendations fetched")

