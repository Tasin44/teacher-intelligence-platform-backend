from django.contrib import admin
from .models import Assignment, AssignmentQuestion, AssignmentMailLog

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("assignment_id", "title", "subject", "teacher", "target_type", "ai_difficulty", "due_date", "creation_date")
    list_filter = ("subject", "target_type", "ai_difficulty", "ai_generation_status", "creation_date")
    search_fields = ("title", "subject", "teacher__first_name", "teacher__last_name", "teacher__email")
    ordering = ("-creation_date",)

@admin.register(AssignmentQuestion)
class AssignmentQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_id", "assignment", "question_order")
    search_fields = ("assignment__title", "question_text")
    ordering = ("assignment", "question_order")

@admin.register(AssignmentMailLog)
class AssignmentMailLogAdmin(admin.ModelAdmin):
    list_display = ("log_id", "assignment", "student", "parent_email", "sent_at")
    list_filter = ("sent_at",)
    search_fields = ("assignment__title", "student__student_name", "parent_email")
    ordering = ("-sent_at",)
