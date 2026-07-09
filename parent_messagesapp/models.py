from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class AIParentMessage(models.Model):
    class Classification(models.TextChoices):
        PROGRESS_UPDATE = "progress_update", "Progress Update"
        CONCERN         = "concern",         "Concern"
        ACHIEVEMENT     = "achievement",     "Achievement"

    class Tone(models.TextChoices):
        FORMAL   = "formal",   "Formal"
        FRIENDLY = "friendly", "Friendly"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT  = "sent",  "Sent"

    message_id     = models.BigAutoField(primary_key=True)
    teacher        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="parent_messages")
    student        = models.ForeignKey("studentapp.Student", on_delete=models.CASCADE,related_name="parent_messages")
    classification = models.CharField(max_length=20, choices=Classification.choices)
    tone           = models.CharField(max_length=10, choices=Tone.choices)
    parent_email   = models.EmailField(max_length=150)
    message_text   = models.TextField()
    status         = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    sent_at        = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_parent_messages"
        indexes  = [
            models.Index(fields=["teacher", "student"]),
            models.Index(fields=["sent_at"]),
        ]
        ordering = ["-created_at"]
