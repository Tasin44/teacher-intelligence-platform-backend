from django.shortcuts import render

# Create your views here.
from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import AssignmentFeedback
from .serializers import AssignmentFeedbackSerializer



