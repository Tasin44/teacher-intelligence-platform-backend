from django.shortcuts import render

# Create your views here.


from rest_framework import status,viewsets
from rest_framework.permissions import IsAuthenticated

from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import Observation
from .serializers import ObservationSerializer



class ObservationViewSet(StandardResponseMixin, viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated, IsOwnerTeacher]
    serializer_class = ObservationSerializer

    def get_throttles(self):
        self.throttle_scope = "read" if self.request.method == "GET" else "write"
        return super().get_throttles()


    def get_queryset(self):
        qs = Observation.objects.filter(student__teacher=self.request.user).select_related("student")
        roll = self.request.query_params.get("student_roll")
        if roll:
            qs = qs.filter(student__student_roll=roll)
        obs_date = self.request.query_params.get("date")
        if obs_date:
            qs = qs.filter(observation_date=obs_date)
        return qs







