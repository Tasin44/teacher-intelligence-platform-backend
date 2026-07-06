from django.conf import settings
from django.db import models


class OffDay(models.Model):
    off_day_id = models.BigAutoField(primary_key=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="off_days")
    off_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "off_days"
        constraints = [models.UniqueConstraint(fields=["teacher", "off_date"], name="uq_teacher_offday")]