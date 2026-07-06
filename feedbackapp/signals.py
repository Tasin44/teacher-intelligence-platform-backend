from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from coreapp.cache_utils import bump_teacher_cache_version
from .models import AssignmentFeedback


def _recalculate_avg_score(student):
    avg = student.assignment_feedback.aggregate(a=Avg("score"))["a"]
    student.avg_score = round(avg, 2) if avg is not None else None
    student.save(update_fields=["avg_score"])
    bump_teacher_cache_version(student.teacher_id)


@receiver(post_save, sender=AssignmentFeedback)
def on_feedback_saved(sender, instance, **kwargs):
    _recalculate_avg_score(instance.student)


@receiver(post_delete, sender=AssignmentFeedback)
def on_feedback_deleted(sender, instance, **kwargs):
    _recalculate_avg_score(instance.student)