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
