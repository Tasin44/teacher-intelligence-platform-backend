from rest_framework import serializers
from .models import OffDay, Attendance


class OffDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OffDay
        fields = ["off_day_id", "off_date"]

    def validate_off_date(self, value):
        teacher = self.context["request"].user
        if OffDay.objects.filter(teacher=teacher, off_date=value).exists():
            raise serializers.ValidationError("This date is already marked as an off day")
        return value