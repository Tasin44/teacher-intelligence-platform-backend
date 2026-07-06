


from django.core.cache import cache
from django.db.models import Avg, Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from coreapp.cache_utils import CACHE_TTL_DASHBOARD, scoped_cache_key
from coreapp.response import StandardResponseMixin
from studentapp.models import Student
from feedbackapp.models import AssignmentFeedback
from .models import ActivityLog






