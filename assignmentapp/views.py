from django.shortcuts import render

# Create your views here.
from django.core.cache import cache
from django.db import transaction 
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filter,status,viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


from coreapp.cache_utils import (CACHE_TTL_LISTS, bump_teacher_cache_version,binary_search_title_prefix, scoped_cache_key)
from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import Assignment, AssignmentQuestion, AssignmentMailLog
