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





