from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("log_id", "teacher", "activity_type", "created_at")
    list_filter = ("activity_type", "created_at")
    search_fields = ("teacher__first_name", "teacher__last_name", "description")
    ordering = ("-created_at",)
