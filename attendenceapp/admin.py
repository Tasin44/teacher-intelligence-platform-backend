from django.contrib import admin
from .models import OffDay, Attendance

@admin.register(OffDay)
class OffDayAdmin(admin.ModelAdmin):
    list_display = ("off_day_id", "teacher", "off_date", "reason", "created_at")
    list_filter = ("off_date",)
    search_fields = ("teacher__first_name", "teacher__last_name", "teacher__email", "reason")
    ordering = ("-off_date",)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("attendance_id", "student", "attendance_date", "status", "created_at")
    list_filter = ("status", "attendance_date")
    search_fields = ("student__student_name", "student__student_roll")
    ordering = ("-attendance_date",)
