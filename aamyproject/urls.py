"""
URL configuration for aamyproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── Admin ─────────────────────────────────────────────
    path("api/admin/", include("adminapp.urls")),

    # ── Auth ──────────────────────────────────────────────
    path("api/auth/", include("authapp.urls")),

    # ── Students ──────────────────────────────────────────
    path("api/students/", include("studentapp.urls")),

    # ── Assignments ───────────────────────────────────────
    path("api/assignments/", include("assignmentapp.urls")),

    # ── Groups ────────────────────────────────────────────
    path("api/groups/", include("groupapp.urls")),

    # ── Dashboard ─────────────────────────────────────────
    path("api/dashboard/", include("dashboardapp.urls")),

    # ── Feedback / Assessments ────────────────────────────
    path("api/feedback/", include("feedbackapp.urls")),

    # ── Attendance ────────────────────────────────────────
    path("api/attendance/", include("attendenceapp.urls")),

    # ── Behavior ──────────────────────────────────────────
    path("api/behavior-feedback/", include("behaviorapp.urls")),

    # ── Observations ──────────────────────────────────────
    path("api/observations/", include("observationsapp.urls")),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
