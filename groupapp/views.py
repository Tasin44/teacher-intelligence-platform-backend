from django.shortcuts import render

# Create your views here.

from django.db import transaction
from django.db.models import Avg, Count, Max
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.cache_utils import bump_teacher_cache_version
from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
# from dashboardapp.models import ActivityLog
from .models import Group, GroupGenerationHistory
from .serializers import GroupSerializer, GroupEditSerializer, GroupGenerationHistorySerializer
from .grouping_service import generate_groups