from django.contrib import admin
from .models import Observation

@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("observation_id", "student", "observation_date", "setting_tag", "created_at")
    list_filter = ("setting_tag", "observation_date")
    search_fields = ("student__student_name", "student__student_roll", "notes")
    ordering = ("-observation_date",)
