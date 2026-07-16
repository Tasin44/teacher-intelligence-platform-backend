from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from coreapp.cache_utils import bump_teacher_cache_version
from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import Student
from .serializers import StudentCreateSerializer, StudentListSerializer
from django.db import models
from rest_framework.views import APIView

class StudentViewSet(StandardResponseMixin, viewsets.ModelViewSet):


    permission_classes = [IsAuthenticated, IsOwnerTeacher]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["risk_status", "student_grade", "recommended_group"]
    search_fields = ["student_name", "student_roll", "student_grade", "parent_name"]
    ordering_fields = ["student_name", "avg_score", "attendance_rate", "created_at"]

    def get_throttles(self):
        self.throttle_scope = "read" if self.request.method in ("GET",) else "write"
        return super().get_throttles()

    def get_queryset(self):
        # select_related avoids an extra query per row for recommended_group
        return (Student.objects
                .filter(teacher=self.request.user)
                .select_related("recommended_group"))

    def get_serializer_class(self):
        return StudentCreateSerializer if self.action in ("create", "update", "partial_update") \
            else StudentListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Could not create student",
                                        status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        student = serializer.save()
        bump_teacher_cache_version(request.user.pk)
        return self.success_response(StudentListSerializer(student, context={"request": request}).data,
                                      "Student created", status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True)
        return self.success_response(self.get_paginated_response(serializer.data).data,
                                      "Students fetched")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return self.success_response(StudentListSerializer(instance, context={"request": request}).data, "Student fetched")


    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.error_response("Update failed", status.HTTP_422_UNPROCESSABLE_ENTITY,
                                        serializer.errors)
        student = serializer.save()
        bump_teacher_cache_version(request.user.pk)
        return self.success_response(StudentListSerializer(student, context={"request": request}).data, "Student updated")


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        bump_teacher_cache_version(request.user.pk)
        return self.success_response(None, "Student deleted")

class StudentSearchView(StandardResponseMixin, APIView):
    """
    GET /api/students/search/?q=...
    Search students based on name, roll, risk status, or parent name.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        qs = Student.objects.filter(teacher=request.user).select_related("recommended_group")
        
        if query:
            qs = qs.filter(
                models.Q(student_name__icontains=query) |
                models.Q(student_roll__icontains=query) |
                models.Q(risk_status__icontains=query) |
                models.Q(parent_name__icontains=query)
            )
        
        return self.success_response(
            StudentListSerializer(qs, many=True, context={"request": request}).data,
            "Search results fetched"
        )


class StudentDiagnosticView(StandardResponseMixin, APIView):
    """
    GET /api/students/{student_id}/diagnostic/
    Uses AI to generate:
      - Current Strengths
      - Skill Gaps & Standards Blockages
    based on the student's full profile (scores, attendance, behavior, observations).
    """
    permission_classes = [IsAuthenticated]
    throttle_scope = "ai_generate"

    def get(self, request, student_id):
        # --- Fetch student (must belong to the requesting teacher) ---
        try:
            student = Student.objects.select_related("recommended_group").get(
                pk=student_id, teacher=request.user
            )
        except Student.DoesNotExist:
            return self.error_response("Student not found.", status.HTTP_404_NOT_FOUND)

        # --- Gather context data from related apps ---
        from behaviorapp.models import BehaviorFeedback
        from observationsapp.models import Observation
        from feedbackapp.models import AssignmentFeedback
        from attendenceapp.models import Attendance

        # Behavior notes (last 10)
        behavior_notes = list(
            BehaviorFeedback.objects.filter(student=student)
            .order_by("-event_date")[:10]
            .values("incident_classification", "observation_note", "event_date")
        )

        # Teacher observations (last 10)
        observations = list(
            Observation.objects.filter(student=student)
            .order_by("-observation_date")[:10]
            .values("setting_tag", "notes", "observation_date")
        )

        # Assignment feedback (last 10 scores)
        feedback = list(
            AssignmentFeedback.objects.filter(student=student)
            .order_by("-assessment_date")[:10]
            .values("subject", "score", "ccss_code", "assessment_date")
        )

        # Recent attendance records
        recent_attendance = list(
            Attendance.objects.filter(student=student)
            .order_by("-attendance_date")[:20]
            .values("attendance_date", "status")
        )

        # --- Build prompt ---
        prompt = f"""
        You are an expert educational diagnostician. Analyze the following data for a student and produce a diagnostic profile.

        STUDENT PROFILE:
        - Name: {student.student_name}
        - Grade: {student.student_grade}
        - Reading Level: {student.reading_level or 'Not Set'}
        - Risk Status: {student.risk_status}
        - Average Score: {student.avg_score or 'N/A'}%
        - Attendance Rate: {student.attendance_rate or 'N/A'}%
        - Recommended Group: {student.recommended_group.group_name if student.recommended_group else 'None'}

        RECENT ASSIGNMENT SCORES (last 10):
        {feedback if feedback else 'No assignment feedback available.'}

        RECENT BEHAVIOR NOTES (last 10):
        {behavior_notes if behavior_notes else 'No behavior records available.'}

        TEACHER OBSERVATIONS (last 10):
        {observations if observations else 'No observations available.'}

        RECENT ATTENDANCE (last 20 days):
        {recent_attendance if recent_attendance else 'No attendance records available.'}

        Based on this data, identify:
        1. Current Strengths (3-4 specific, positive bullet points about what this student does well)
        2. Skill Gaps & Standards Blockages (3-4 specific bullet points of what this student struggles with, including CCSS standards references where relevant)

        Return ONLY a valid JSON object in this exact format:
        {{
            "current_strengths": [
                "strength 1",
                "strength 2",
                "strength 3"
            ],
            "skill_gaps_and_blockages": [
                "gap/blockage 1",
                "gap/blockage 2",
                "gap/blockage 3"
            ],
            "generated_at": "ISO datetime string"
        }}
        """

        # --- Call AI ---
        from coreapp.ai_utils import call_openai_with_retry, AIServiceError
        from django.utils import timezone

        try:
            ai_result = call_openai_with_retry(
                messages=[
                    {"role": "system", "content": "You are an expert educational diagnostician. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=700,
            )
        except AIServiceError as e:
            return self.error_response(str(e), status.HTTP_503_SERVICE_UNAVAILABLE)

        # --- Build response ---
        response_data = {
            "student": StudentListSerializer(student, context={"request": request}).data,
            "diagnostic": {
                "current_strengths": ai_result.get("current_strengths", []),
                "skill_gaps_and_blockages": ai_result.get("skill_gaps_and_blockages", []),
                "generated_at": ai_result.get("generated_at", timezone.now().isoformat()),
            }
        }

        return self.success_response(response_data, "Student diagnostic generated successfully.")
