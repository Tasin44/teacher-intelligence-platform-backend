from django.contrib import admin
from .models import Teacher, OTPVerification

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("teacher_id", "email", "first_name", "last_name", "school", "approval_status", "is_active", "is_verified", "created_at")
    list_filter = ("is_active", "is_verified", "is_staff", "approval_status", "school")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)
    actions = ["approve_teachers"]
    
    @admin.action(description="Approve selected teachers")
    def approve_teachers(self, request, queryset):
        updated = queryset.update(approval_status="approved", is_active=True)
        self.message_user(request, f"Successfully approved {updated} teacher(s).")
    
@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ("id", "identifier", "otp_code", "purpose", "is_verified", "expires_at", "created_at")
    list_filter = ("purpose", "is_verified")
    search_fields = ("identifier",)
    ordering = ("-created_at",)
