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


