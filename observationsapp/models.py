from django.db import models

class Observation(models.Model):
    class SettingTag(models.TextChoices):
        SMALL_GROUP = "small_group", "Small Group"
        ONE_TO_ONE = "one_to_one", "1:1"
        WHOLE_CLASS = "whole_class", "Whole Class"

    observation_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("studentapp.Student", on_delete=models.CASCADE,related_name="observations", db_index=True)
    observation_date = models.DateField()
    setting_tag = models.CharField(max_length=15, choices=SettingTag.choices)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "observations"
        indexes = [models.Index(fields=["student", "observation_date"])]
        ordering = ["-observation_date"]
