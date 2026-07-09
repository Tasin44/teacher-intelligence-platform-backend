from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.response import StandardResponseMixin
from assignmentapp.models import Assignment
from .models import PacingRecommendation
from .serializers import PacingRecommendationSerializer
from .services import PacingError, generate_pacing_recommendation


class GeneratePacingView(StandardResponseMixin, APIView):
    """
    POST /api/pacing/generate/{assignment_id}
    AI generates curriculum adjustment + standards coverage checklist
    based on this assignment's topic, CCSS code, and class performance.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "ai_generate"

    def post(self, request, assignment_id):
        try:
            assignment = Assignment.objects.get(pk=assignment_id, teacher=request.user)
        except Assignment.DoesNotExist:
            return self.error_response("Assignment not found", status.HTTP_404_NOT_FOUND)

        try:
            result = generate_pacing_recommendation(assignment, request.user)
        except PacingError as exc:
            return self.error_response(f"AI pacing generation failed: {exc}",status.HTTP_502_BAD_GATEWAY)

        rec = PacingRecommendation.objects.create(
            teacher    = request.user,
            assignment = assignment,
            topic      = assignment.title,
            **result,
        )
        return self.success_response(PacingRecommendationSerializer(rec).data,"Pacing recommendation generated", status.HTTP_201_CREATED)


class PacingListView(StandardResponseMixin, APIView):
    """
    GET /api/pacing/?topic=<keyword>
    Returns all pacing recommendations for this teacher, optionally filtered by topic.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request):
        qs = PacingRecommendation.objects.filter(teacher=request.user).select_related("assignment")
        if topic := request.query_params.get("topic", "").strip():
            qs = qs.filter(topic__icontains=topic)
        return self.success_response(PacingRecommendationSerializer(qs, many=True).data,"Pacing recommendations fetched")