from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    class ActivityType(models.TextChoices):
        ASSIGNMENT_CREATED = "assignment_created", "Assignment Created"
        ASSIGNMENT_SUBMITTED = "assignment_submitted", "Assignment Submitted"
        MAIL_SENT = "mail_sent", "Mail Sent"
        GROUP_GENERATED = "group_generated", "Group Generated"
        INTERVENTION_CREATED = "intervention_created", "Intervention Created"
        OBSERVATION_ADDED = "observation_added", "Observation Added"
        ATTENDANCE_MARKED = "attendance_marked", "Attendance Marked"
        FEEDBACK_ADDED = "feedback_added", "Feedback Added"
        MESSAGE_SENT = "message_sent", "Message Sent"

    activity_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="activities", db_index=True)
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    description = models.CharField(max_length=255)
    reference_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_log"
        indexes = [models.Index(fields=["teacher", "-created_at"])]
        ordering = ["-created_at"]












