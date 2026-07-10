from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.response import StandardResponseMixin
from .models import AIParentMessage
from .serializers import GenerateMessageSerializer, AIParentMessageSerializer
from .services import ParentMessageError, generate_parent_message, send_parent_email


class GenerateParentMessageView(StandardResponseMixin, APIView):
    """
    POST /api/parent-messages/generate
    Body: { student_roll, classification, tone }
    Calls OpenAI → saves draft message → returns it.
    Teacher can then call /send/{id} or download as PDF from the draft.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "ai_generate"

    def post(self, request):
        serializer = GenerateMessageSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Validation failed",status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)

        student        = serializer._student
        classification = serializer.validated_data["classification"]
        tone           = serializer.validated_data["tone"]

        try:
            message_text = generate_parent_message(student, classification, tone)
        except ParentMessageError as exc:
            return self.error_response(f"AI generation failed: {exc}", status.HTTP_502_BAD_GATEWAY)

        msg = AIParentMessage.objects.create(
            teacher        = request.user,
            student        = student,
            classification = classification,
            tone           = tone,
            parent_email   = student.parent_email,
            message_text   = message_text,
            status         = AIParentMessage.Status.DRAFT,
        )
        return self.success_response(AIParentMessageSerializer(msg).data,"Message generated successfully", status.HTTP_201_CREATED)


class SendParentMessageView(StandardResponseMixin, APIView):
    """
    POST /api/parent-messages/{message_id}/send
    Sends the drafted message to the parent email.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "write"

    def post(self, request, message_id):
        try:
            msg = AIParentMessage.objects.select_related("student").get(
                pk=message_id, teacher=request.user)
        except AIParentMessage.DoesNotExist:
            return self.error_response("Message not found", status.HTTP_404_NOT_FOUND)

        if msg.status == AIParentMessage.Status.SENT:
            return self.error_response("Message already sent", status.HTTP_400_BAD_REQUEST)

        send_parent_email(msg.parent_email, msg.student.student_name, msg.message_text)

        msg.status  = AIParentMessage.Status.SENT
        msg.sent_at = timezone.now()
        msg.save(update_fields=["status", "sent_at"])

        return self.success_response(AIParentMessageSerializer(msg).data,"Message sent to parent")




class ParentMessageListView(StandardResponseMixin, APIView):
    """
    GET /api/parent-messages/
    ?student_roll=  ?classification=  ?status=draft|sent
    """
    permission_classes = [IsAuthenticated]
    throttle_scope     = "read"

    def get(self, request):
        qs = (AIParentMessage.objects
              .filter(teacher=request.user)
              .select_related("student"))
        if roll := request.query_params.get("student_roll"):
            qs = qs.filter(student__student_roll=roll)
        if clf := request.query_params.get("classification"):
            qs = qs.filter(classification=clf)
        if st := request.query_params.get("status"):
            qs = qs.filter(status=st)

        return self.success_response(
            AIParentMessageSerializer(qs, many=True).data,
            "Parent messages fetched")

class DownloadParentMessagePDFView(StandardResponseMixin, APIView):
    """
    GET /api/parent-messages/{message_id}/download-pdf
    Generates and downloads the parent message as a PDF file.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope = "read"

    def get(self, request, message_id):
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from textwrap import wrap
        import io

        try:
            msg = AIParentMessage.objects.select_related("student").get(
                pk=message_id, teacher=request.user)
        except AIParentMessage.DoesNotExist:
            return self.error_response("Message not found", status.HTTP_404_NOT_FOUND)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Parent Message")
        
        # Details
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Student: {msg.student.student_name}")
        p.drawString(50, height - 100, f"Classification: {msg.classification.title()}")
        p.drawString(50, height - 120, f"Date: {msg.created_at.strftime('%B %d, %Y')}")

        # Message Text
        y = height - 160
        p.setFont("Helvetica", 12)
        for p_text in msg.message_text.split('\n'):
            if p_text.strip():
                for line in wrap(p_text, width=80):
                    if y < 50:
                        p.showPage()
                        y = height - 50
                        p.setFont("Helvetica", 12)
                    p.drawString(50, y, line)
                    y -= 20
            else:
                y -= 10

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="parent_message_{message_id}.pdf"'
        return response


