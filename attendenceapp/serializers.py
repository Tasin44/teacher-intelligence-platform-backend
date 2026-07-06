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

    def create(self, validated_data):
        validated_data["teacher"] = self.context["request"].user
        return super().create(validated_data)


class AttendanceSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(write_only=True)

    class Meta:
        model = Attendance
        fields = ["attendance_id", "student_roll", "attendance_date", "status"]

    def validate(self, attrs):
        teacher = self.context["request"].user
        from studentapp.models import Student
        roll = attrs.get("student_roll")
        try:
            self._student = Student.objects.get(teacher=teacher, student_roll=roll)
        except Student.DoesNotExist:
            raise serializers.ValidationError({"student_roll": "No such student for this teacher"})

        attendance_date = attrs.get("attendance_date")
        if attendance_date and OffDay.objects.filter(teacher=teacher, off_date=attendance_date).exists():
            raise serializers.ValidationError({"attendance_date": "This date is marked as an off day"})
        if attendance_date and attendance_date.weekday() == 6:  # Sunday excluded per spec (Mon-Sun w/ off-day)
            pass  # spec explicitly allows Mon-Sun excluding off days; Sunday is allowed unless marked off
        return attrs

    def create(self, validated_data):
        validated_data.pop("student_roll")
        student = self._student
        attendance, _ = Attendance.objects.update_or_create(
            student=student, attendance_date=validated_data["attendance_date"],
            defaults={"status": validated_data["status"]},
        )
        return attendance




















