from django.shortcuts import render

# Create your views here.


from rest_framework import status,viewsets
from rest_framework.permissions import IsAuthenticated

from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import BehaviorFeedback
from .serializers import BehaviorFeedbackSerializer



class BehaviorFeedbackViewSet(StandardResponseMixin, viewsets.ModelViewSet):


    permission_classes = [IsAuthenticated, IsOwnerTeacher]
    serializer_class = BehaviorFeedbackSerializer

    def get_throttles(self):
        self.throttle_scope = "read" if self.request.method == "GET" else "write"
        return super().get_throttles()

    def get_queryset(self):
        qs = BehaviorFeedback.objects.filter(student__teacher=self.request.user).select_related("student")
        roll = self.request.query_params.get("student_roll")
        if roll:
            qs = qs.filter(student__student_roll=roll)
        return qs

