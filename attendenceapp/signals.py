from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from coreapp.cache_utils import bump_teacher_cache_version
from .models import Attendance


def _recalculate_attendance_rate(student):
    qs = student.attendance_records.all()
    total = qs.count()
    if total == 0:
        student.attendance_rate = None
    else:
        present_or_late = qs.filter(status__in=["present", "late"]).count()
        student.attendance_rate = round((present_or_late / total) * 100, 2)
    student.save(update_fields=["attendance_rate"])
    bump_teacher_cache_version(student.teacher_id)


@receiver(post_save, sender=Attendance)
def on_attendance_saved(sender, instance, **kwargs):
    _recalculate_attendance_rate(instance.student)


@receiver(post_delete, sender=Attendance)
def on_attendance_deleted(sender, instance, **kwargs):
    _recalculate_attendance_rate(instance.student)
