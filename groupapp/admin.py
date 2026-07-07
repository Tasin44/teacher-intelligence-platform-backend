from django.contrib import admin
from .models import Group, GroupStudent, GroupGenerationHistory

class GroupStudentInline(admin.TabularInline):
    model = GroupStudent
    extra = 0

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("group_id", "teacher", "group_name", "classification", "tag", "avg_score", "generated_by_ai", "generated_at")
    list_filter = ("classification", "tag", "generated_by_ai", "generated_at")
    search_fields = ("group_name", "teacher__first_name", "teacher__last_name")
    ordering = ("-generated_at",)
    inlines = [GroupStudentInline]

@admin.register(GroupStudent)
class GroupStudentAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "student", "added_at")
    search_fields = ("group__group_name", "student__student_name")
    ordering = ("-added_at",)

@admin.register(GroupGenerationHistory)
class GroupGenerationHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "teacher", "group", "classification", "generated_date")
    list_filter = ("classification", "generated_date")
    search_fields = ("teacher__first_name", "teacher__last_name")
    ordering = ("-generated_date",)
