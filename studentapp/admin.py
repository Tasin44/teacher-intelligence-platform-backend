from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "student_name", "student_roll", "teacher", "student_grade", "risk_status", "avg_score", "attendance_rate", "created_at")
    list_filter = ("risk_status", "student_grade", "created_at")
    search_fields = ("student_name", "student_roll", "teacher__first_name", "teacher__last_name", "parent_email")
    ordering = ("-created_at",)
