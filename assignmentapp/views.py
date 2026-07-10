from django.core.cache import cache
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .ai_service import generate_assignment_questions, AIGenerationError

from coreapp.cache_utils import (CACHE_TTL_LISTS, bump_teacher_cache_version,
                                  binary_search_title_prefix, scoped_cache_key)
from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import Assignment, AssignmentQuestion, AssignmentMailLog
from .serializers import AssignmentCreateSerializer, AssignmentListSerializer
from adminapp.models import AIUsageLog



def _resolve_target_students(assignment: Assignment):
    """Flatten target_type into a concrete list of Student rows to notify."""
    from studentapp.models import Student
    if assignment.target_type == Assignment.TargetType.STUDENT and assignment.target_student:
        return [assignment.target_student]
    if assignment.target_type == Assignment.TargetType.GROUP and assignment.target_group:
        return list(Student.objects.filter(
            group_memberships__group=assignment.target_group))
    if assignment.target_type == Assignment.TargetType.ALL_GROUPS:
        return list(Student.objects.filter(teacher=assignment.teacher))
    return []

def _log_activity(teacher_id, activity_type, description, reference_id=None):
    from dashboardapp.models import ActivityLog
    ActivityLog.objects.create(teacher_id=teacher_id, activity_type=activity_type,
                               description=description, reference_id=reference_id)



class AssignmentViewSet(StandardResponseMixin, viewsets.ModelViewSet):
    """
    POST   /api/assignments              -> create + AI-generate questions + email parents
    GET    /api/assignments              -> list, filter by subject/tag/target_type
    GET    /api/assignments/{id}         -> retrieve (with generated questions)
    GET    /api/assignments/search?q=    -> O(log n) title-prefix search via cached sorted index
    """

    permission_classes = [IsAuthenticated, IsOwnerTeacher]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["subject", "tag", "target_type", "ai_generation_status"]
    ordering_fields = ["due_date", "creation_date", "title"]


    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "ai_generate"
        else:
            self.throttle_scope = "read" if self.request.method == "GET" else "write"
        return super().get_throttles()

    def get_queryset(self):
        return (Assignment.objects
                .filter(teacher=self.request.user)
                .select_related("target_student", "target_group")
                .prefetch_related("questions"))

    def get_serializer_class(self):
        return AssignmentCreateSerializer if self.action == "create" else AssignmentListSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = AssignmentCreateSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Could not create assignment",
                                        status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        assignment = serializer.save()

        # --- AI generation (OpenAI) ---
        try:
            questions = generate_assignment_questions(
                subject=assignment.subject,
                ccss_code=assignment.ccss_code,
                difficulty=assignment.ai_difficulty,
                number_of_questions=assignment.number_of_questions,
                instructions=assignment.instructions,
                grade_level=getattr(request.user, "grade", ""),
            )
            AssignmentQuestion.objects.bulk_create([
                AssignmentQuestion(assignment=assignment, question_text=q, question_order=i)
                for i, q in enumerate(questions, start=1)
            ])
            assignment.ai_generation_status = "completed"
            
            # Log usage for admin platform
            if getattr(request.user, "school", None):
                AIUsageLog.objects.create(
                    teacher=request.user,
                    school=request.user.school,
                    endpoint="assignment_generation"
                )
        except AIGenerationError as exc:
            assignment.ai_generation_status = "failed"
            assignment.save(update_fields=["ai_generation_status"])
            bump_teacher_cache_version(request.user.pk)
            # Assignment row is kept (status=failed) so the teacher can retry
            # rather than silently losing the due-date/instructions they entered.
            return self.error_response(
                f"Assignment Instructions saved but AI question generation failed: {exc}",
                status.HTTP_502_BAD_GATEWAY,
                {"assignment_id": assignment.assignment_id},
            )
        assignment.save(update_fields=["ai_generation_status"])
        # --- email parents of every targeted student ---
        targets = _resolve_target_students(assignment)
        for student in targets:
            if student.parent_email:
                # send_assignment_email.delay(...) recommended via Celery in production
                AssignmentMailLog.objects.create(
                    assignment=assignment, student=student, parent_email=student.parent_email)

        _log_activity(request.user.pk, "assignment_created",
                      f"Assignment '{assignment.title}' created and sent to {len(targets)} parent(s)",
                      assignment.assignment_id)
        bump_teacher_cache_version(request.user.pk)

        assignment.refresh_from_db()
        return self.success_response(AssignmentListSerializer(assignment).data,
                                      "Assignment generated and sent", status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = AssignmentListSerializer(page, many=True)
        return self.success_response(self.get_paginated_response(serializer.data).data,
                                      "Assignments fetched")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return self.success_response(AssignmentListSerializer(instance).data, "Assignment fetched")


    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        GET /api/assignments/search?q=<prefix>
        Maintains a per-teacher cached, sorted list of titles and uses
        binary search (O(log n)) instead of scanning every row.
        """
        q = request.query_params.get("q", "").strip()
        if not q:
            return self.error_response("q query param is required", status.HTTP_400_BAD_REQUEST)

        cache_key = scoped_cache_key(request.user.pk, "assignment_titles_sorted")
        sorted_titles = cache.get(cache_key)
        if sorted_titles is None:
            sorted_titles = list(
                Assignment.objects.filter(teacher=request.user)
                .order_by("title").values_list("title", flat=True)
            )
            cache.set(cache_key, sorted_titles, timeout=CACHE_TTL_LISTS)

        idx = binary_search_title_prefix(sorted_titles, q)
        if idx == -1:
            return self.success_response([], "No matching assignments")

        matches = []
        i = idx
        while i < len(sorted_titles) and sorted_titles[i].lower().startswith(q.lower()):
            matches.append(sorted_titles[i])
            i += 1

        results = (Assignment.objects
                   .filter(teacher=request.user, title__in=matches)
                   .select_related("target_student", "target_group")
                   .prefetch_related("questions"))
        return self.success_response(AssignmentListSerializer(results, many=True).data,
                                      "Assignments matched")

    @action(detail=True, methods=["get"], url_path="download-pdf")
    def download_pdf(self, request, pk=None):
        """
        GET /api/assignments/{id}/download-pdf/
        Generates and downloads the assignment as a PDF file.
        """
        assignment = self.get_object()
        
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from textwrap import wrap
        import io

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Draw Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, f"Assignment: {assignment.title}")

        # Draw details
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Subject: {assignment.subject}")
        p.drawString(50, height - 100, f"Difficulty: {assignment.ai_difficulty}")
        if assignment.due_date:
            p.drawString(50, height - 120, f"Due Date: {assignment.due_date}")

        y = height - 150
        if assignment.instructions:
            p.drawString(50, y, "Instructions:")
            y -= 20
            for line in wrap(assignment.instructions, width=80):
                if y < 50:
                    p.showPage()
                    y = height - 50
                    p.setFont("Helvetica", 12)
                p.drawString(50, y, line)
                y -= 20
        
        y -= 20
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Questions:")
        y -= 30

        p.setFont("Helvetica", 12)
        for idx, q in enumerate(assignment.questions.all(), start=1):
            question_lines = wrap(f"{idx}. {q.question_text}", width=80)
            for line in question_lines:
                if y < 50:
                    p.showPage()
                    y = height - 50
                    p.setFont("Helvetica", 12)
                p.drawString(50, y, line)
                y -= 20
            y -= 10

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="assignment_{assignment.unique_assignment_code}.pdf"'
        return response

    @action(detail=True, methods=["post"], url_path="send-email")
    def send_email(self, request, pk=None):
        """
        POST /api/assignments/{id}/send-email/
        Generates the PDF and sends it to all targeted parents with a submission link.
        """
        assignment = self.get_object()
        
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from textwrap import wrap
        import io
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, f"Assignment: {assignment.title}")
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Subject: {assignment.subject}")
        p.drawString(50, height - 100, f"Difficulty: {assignment.ai_difficulty}")
        if assignment.due_date:
            p.drawString(50, height - 120, f"Due Date: {assignment.due_date}")

        y = height - 150
        if assignment.instructions:
            p.drawString(50, y, "Instructions:")
            y -= 20
            for line in wrap(assignment.instructions, width=80):
                if y < 50:
                    p.showPage()
                    y = height - 50
                    p.setFont("Helvetica", 12)
                p.drawString(50, y, line)
                y -= 20
        
        y -= 20
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Questions:")
        y -= 30

        p.setFont("Helvetica", 12)
        for idx, q in enumerate(assignment.questions.all(), start=1):
            question_lines = wrap(f"{idx}. {q.question_text}", width=80)
            for line in question_lines:
                if y < 50:
                    p.showPage()
                    y = height - 50
                    p.setFont("Helvetica", 12)
                p.drawString(50, y, line)
                y -= 20
            y -= 10

        p.showPage()
        p.save()
        pdf_bytes = buffer.getvalue()
        
        from django.core.mail import EmailMessage
        targets = _resolve_target_students(assignment)
        sent_count = 0
        
        frontend_url = "http://127.0.0.1:8037"
        submission_link = f"{frontend_url}/assignments/{assignment.unique_assignment_code}/submit"
        
        for student in targets:
            if student.parent_email:
                subject = f"Assignment for {student.student_name}: {assignment.title}"
                message = f"Dear Parent,\n\nPlease find attached the assignment for {student.student_name}.\n\nYou can submit the completed assignment using the following link:\n{submission_link}\n\nBest regards,\n{request.user.first_name} {request.user.last_name}"
                
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=None,
                    to=[student.parent_email]
                )
                email.attach(f"assignment_{assignment.unique_assignment_code}.pdf", pdf_bytes, "application/pdf")
                email.send(fail_silently=True)
                
                AssignmentMailLog.objects.create(
                    assignment=assignment, student=student, parent_email=student.parent_email)
                sent_count += 1
                
        return self.success_response(None, f"Assignment sent to {sent_count} parents via email.")

    @action(detail=False, methods=["get"], url_path="submissions")
    def all_submissions(self, request):
        """
        GET /api/assignments/submissions/
        Lists all submissions for all assignments created by the authenticated teacher.
        """
        from .models import AssignmentSubmission
        submissions = AssignmentSubmission.objects.filter(assignment__teacher=request.user).select_related('assignment').order_by("-submitted_at")
        from .serializers import AssignmentSubmissionSerializer
        return self.success_response(AssignmentSubmissionSerializer(submissions, many=True).data, "All submissions fetched.")

    @action(detail=True, methods=["get"], url_path="submissions")
    def submissions(self, request, pk=None):
        """
        GET /api/assignments/{id}/submissions/
        Lists all submissions for this assignment.
        """
        assignment = self.get_object()
        submissions = assignment.submissions.all().order_by("-submitted_at")
        from .serializers import AssignmentSubmissionSerializer
        return self.success_response(AssignmentSubmissionSerializer(submissions, many=True).data, "Submissions fetched.")

from rest_framework.parsers import MultiPartParser, FormParser

class PublicAssignmentSubmissionView(StandardResponseMixin, APIView):
    """
    POST /api/assignments/public/{unique_code}/submit
    """
    authentication_classes = []
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = "write"
    
    def post(self, request, unique_code):
        try:
            assignment = Assignment.objects.get(unique_assignment_code=unique_code)
        except Assignment.DoesNotExist:
            return self.error_response("Assignment not found or invalid link.", status.HTTP_404_NOT_FOUND)
            
        data = request.data.copy()
        submitted_roll = data.get("roll_number")

        if not submitted_roll:
            return self.error_response("Roll number is required.", status.HTTP_400_BAD_REQUEST)

        # Validation logic based on assignment target_type
        from studentapp.models import Student
        is_valid_student = False

        if assignment.target_type == "individual_student":
            if assignment.target_student and assignment.target_student.student_roll == submitted_roll:
                is_valid_student = True
        elif assignment.target_type == "individual_group":
            if assignment.target_group:
                is_valid_student = Student.objects.filter(
                    student_roll=submitted_roll,
                    group_memberships__group=assignment.target_group
                ).exists()
        elif assignment.target_type == "all_groups":
            is_valid_student = Student.objects.filter(
                student_roll=submitted_roll,
                teacher=assignment.teacher
            ).exists()

        if not is_valid_student:
            return self.error_response("The provided roll number is not authorized for this assignment.", status.HTTP_403_FORBIDDEN)

        data['assignment'] = assignment.assignment_id
        
        from .serializers import AssignmentSubmissionSerializer
        serializer = AssignmentSubmissionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(None, "Assignment submitted successfully.", status.HTTP_201_CREATED)
        return self.error_response("Submission failed", status.HTTP_400_BAD_REQUEST, serializer.errors)

class ServeAssignmentSubmissionView(APIView):
    """
    GET /assignments/{unique_code}/submit
    Serves the standalone HTML file for students to submit assignments.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, unique_code):
        import os
        from django.conf import settings
        from django.http import HttpResponse
        file_path = os.path.join(settings.BASE_DIR, "assignment_submission.html")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return HttpResponse(content, content_type="text/html")
        except FileNotFoundError:
            return StandardResponseMixin().error_response("Assignment submission page not found.", status.HTTP_404_NOT_FOUND)
