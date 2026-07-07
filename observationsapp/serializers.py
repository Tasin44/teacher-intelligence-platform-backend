from datetime import date
from rest_framework import serializers
from .models import Observation


class ObservationSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(write_only=True)

    class Meta:
        model = Observation
        fields = ["observation_id", "student_roll", "observation_date", "setting_tag", "notes"]


    def validate_observation_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("observation_date cannot be in the future")
        return value