from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters,status,viewsets
from rest_framework.permissions import IsAuthenticated

from coreapp.cache_utils import bump_teacher_cache_version
from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import Student
from .serializers import StudentCreateSerializer,StudentListSerializer

class StudentViewSet(StandardResponseMixin, viewsets.ModelViewSet):


    pass








