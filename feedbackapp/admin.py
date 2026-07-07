from django.contrib import admin
from .models import AssignmentFeedback

@admin.register(AssignmentFeedback)
class AssignmentFeedbackAdmin(admin.ModelAdmin):
    list_display = ("feedback_id", "student", "assignment", "subject", "score", "status", "created_at")
    list_filter = ("status", "subject", "created_at")
    search_fields = ("student__student_name", "title")
    ordering = ("-created_at",)
