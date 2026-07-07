from django.contrib import admin
from .models import School, AIConfiguration, AIUsageLog

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("school_id", "school_name", "region_district_office", "registration_status", "created_at")
    list_filter = ("registration_status",)
    search_fields = ("school_name", "region_district_office")
    ordering = ("school_name",)

@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = ("id", "ai_model", "temperature", "max_tokens", "updated_at")

@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ("log_id", "teacher", "school", "endpoint", "tokens_used", "created_at")
    list_filter = ("endpoint", "school", "created_at")
    search_fields = ("teacher__first_name", "teacher__last_name", "school__school_name")
    ordering = ("-created_at",)
