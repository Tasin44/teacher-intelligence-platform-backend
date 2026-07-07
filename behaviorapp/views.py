from django.shortcuts import render

# Create your views here.


from rest_framework import status,viewsets
from rest_framework.permissions import IsAuthenticated

from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import BehaviorFeedback
from .serializers import BehaviorFeedbackSerializer



class BehaviorFeedbackViewSet(StandardResponseMixin, viewsets.ModelViewSet):

    """
    POST   /api/behavior-feedback                  -> create
    GET    /api/behavior-feedback?student_roll=R1   -> list for one student
    PATCH  /api/behavior-feedback/{id}
    DELETE /api/behavior-feedback/{id}
    """
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Could not save behavior feedback",status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        row = serializer.save()
        return self.success_response(BehaviorFeedbackSerializer(row).data,"Behavior feedback recorded", status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page, many=True)
        return self.success_response(self.get_paginated_response(serializer.data).data,"Behavior feedback fetched")

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True,context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Update failed", status.HTTP_422_UNPROCESSABLE_ENTITY,serializer.errors)
        row = serializer.save()
        return self.success_response(BehaviorFeedbackSerializer(row).data, "Row updated")

    def destroy(self, request, *args, **kwargs):
        instance=self.get_object()
        instance.delete()
        return self.success_response(None, "Row deleted")