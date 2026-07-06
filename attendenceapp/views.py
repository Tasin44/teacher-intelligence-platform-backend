from django.shortcuts import render

# Create your views here.
from calendar import monthrange
from datetime import date

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.cache_utils import bump_teacher_cache_version
from coreapp.response import StandardResponseMixin
from .models import Attendance, OffDay
from .serializers import AttendanceSerializer, OffDaySerializer


class OffDayView(StandardResponseMixin, APIView):
    """POST /api/attendance/off-day"""
    permission_classes = [IsAuthenticated]
    throttle_scope = "write"

    def post(self, request):
        serializer = OffDaySerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Could not create off day",status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        off_day = serializer.save()
        bump_teacher_cache_version(request.user.id)
        return self.success_response(OffDaySerializer(off_day).data, "Off day created",status.HTTP_201_CREATED)



class AttendanceView(StandardResponseMixin, APIView):

    permission_classes = [IsAuthenticated]
    throttle_scope = "write"



