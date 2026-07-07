from django.contrib import admin
from .models import BehaviorFeedback

@admin.register(BehaviorFeedback)
class BehaviorFeedbackAdmin(admin.ModelAdmin):
    list_display = ("behavior_id", "student", "event_date", "incident_classification", "engagement_rating", "created_at")
    list_filter = ("incident_classification", "engagement_rating", "event_date")
    search_fields = ("student__student_name", "student__student_roll")
    ordering = ("-event_date",)
