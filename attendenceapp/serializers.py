from rest_framework import serializers
from .models import OffDay, Attendance


class OffDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OffDay
        fields = ["off_day_id", "off_date"]