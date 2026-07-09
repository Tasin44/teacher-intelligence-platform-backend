from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated

from coreapp.permissions import IsOwnerTeacher
from coreapp.response import StandardResponseMixin
from .models import Intervention
from .serializers import InterventionSerializer


class InterventionViewSet(StandardResponseMixin, viewsets.ModelViewSet):
    """
    POST   /api/interventions/              -> create
    GET    /api/interventions/              -> list  (?target_type=individual_student|individual_group)
    GET    /api/interventions/{id}/         -> retrieve
    PATCH  /api/interventions/{id}/         -> partial update
    DELETE /api/interventions/{id}/         -> delete
    """
    permission_classes = [IsAuthenticated, IsOwnerTeacher]
    serializer_class   = InterventionSerializer
    http_method_names  = ["get", "post", "patch", "delete", "head", "options"]

    def get_throttles(self):
        self.throttle_scope = "read" if self.request.method == "GET" else "write"
        return super().get_throttles()

    def get_queryset(self):
        qs = (Intervention.objects
              .filter(teacher=self.request.user)
              .select_related("student", "group"))
        target_type = self.request.query_params.get("target_type")
        if target_type:
            qs = qs.filter(target_type=target_type)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Could not create intervention",status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        obj = serializer.save()
        return self.success_response(InterventionSerializer(obj).data,"Intervention created", status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        return self.success_response(
            self.get_paginated_response(self.get_serializer(page, many=True).data).data,
            "Interventions fetched")

    def retrieve(self, request, *args, **kwargs):
        return self.success_response(self.get_serializer(self.get_object()).data,"Intervention fetched")

    def partial_update(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True,context={"request": request})
        if not serializer.is_valid():
            return self.error_response("Update failed", status.HTTP_422_UNPROCESSABLE_ENTITY,serializer.errors)
        return self.success_response(InterventionSerializer(serializer.save()).data,"Intervention updated")

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return self.success_response(None, "Intervention deleted")
