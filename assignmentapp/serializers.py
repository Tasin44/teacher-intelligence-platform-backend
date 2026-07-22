
from datetime import date
from rest_framework import serializers
from .models import Assignment, AssignmentQuestion


class AssignmentCreateSerializer(serializers.ModelSerializer):
    target_student_roll = serializers.CharField(write_only=True, required=False, allow_blank=True)
    target_group_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Assignment
        fields = [
            "title", "subject", "target_type", "target_student_roll", "target_group_id",
            "ai_difficulty", "ccss_code", "due_date", "instructions", "number_of_questions",
        ]

    def validate_number_of_questions(self, value):
        if not (1 <= value <= 50):
            raise serializers.ValidationError("number_of_questions must be between 1 and 50")
        return value

    def validate_due_date(self, value):
        if value and value < date.today():
            raise serializers.ValidationError("due_date cannot be in the past")
        return value

    def validate(self, attrs):
        target_type = attrs.get("target_type")
        if target_type == Assignment.TargetType.STUDENT and not attrs.get("target_student_roll"):
            raise serializers.ValidationError(
                {"target_student_roll": "Required when target_type is individual_student"})
        if target_type == Assignment.TargetType.GROUP and not attrs.get("target_group_id"):
            raise serializers.ValidationError(
                {"target_group_id": "Required when target_type is individual_group"})
        return attrs

    def create(self, validated_data):
        from studentapp.models import Student
        from groupapp.models import Group

        teacher = self.context["request"].user
        roll = validated_data.pop("target_student_roll", None)
        group_id = validated_data.pop("target_group_id", None)
        target_student, target_group = None, None

        if roll:
            try:
                target_student = Student.objects.get(teacher=teacher, student_roll=roll)
            except Student.DoesNotExist:
                raise serializers.ValidationError({"target_student_roll": "No such student for this teacher"})
        if group_id:
            try:
                target_group = Group.objects.get(teacher=teacher, pk=group_id)
            except Group.DoesNotExist:
                raise serializers.ValidationError({"target_group_id": "No such group for this teacher"})

        return Assignment.objects.create(
            teacher=teacher, target_student=target_student, target_group=target_group,
            **validated_data
        )

    def update(self, instance, validated_data):
        from studentapp.models import Student
        from groupapp.models import Group

        teacher = self.context["request"].user

        if "target_student_roll" in validated_data:
            roll = validated_data.pop("target_student_roll")
            if roll:
                try:
                    instance.target_student = Student.objects.get(teacher=teacher, student_roll=roll)
                except Student.DoesNotExist:
                    raise serializers.ValidationError({"target_student_roll": "No such student"})
            else:
                instance.target_student = None

        if "target_group_id" in validated_data:
            group_id = validated_data.pop("target_group_id")
            if group_id:
                try:
                    instance.target_group = Group.objects.get(teacher=teacher, pk=group_id)
                except Group.DoesNotExist:
                    raise serializers.ValidationError({"target_group_id": "No such group"})
            else:
                instance.target_group = None

        # Update remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AssignmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentQuestion
        fields = ["question_id", "question_text", "question_order"]


class AssignmentListSerializer(serializers.ModelSerializer):
    questions = AssignmentQuestionSerializer(many=True, read_only=True)
    target_student_name = serializers.CharField(source="target_student.student_name", read_only=True, default=None)
    target_group_name = serializers.CharField(source="target_group.group_name", read_only=True, default=None)

    class Meta:
        model = Assignment
        fields = [
            "assignment_id", "title", "subject", "target_type", "target_student_name",
            "target_group_name", "ai_difficulty", "ccss_code", "creation_date", "due_date",
            "instructions", "number_of_questions", "unique_assignment_code", "tag",
            "ai_generation_status", "questions",
        ]


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)

    class Meta:
        from .models import AssignmentSubmission
        model = AssignmentSubmission
        fields = [
            "submission_id", "assignment", "assignment_title", "student_name", "roll_number",
            "grade", "parent_name", "attachment", "attachment_url", "submitted_at",
        ]
        read_only_fields = ["submission_id", "submitted_at"]
        extra_kwargs = {
            "attachment": {"write_only": True}
        }

    def get_attachment_url(self, obj):
        if obj.attachment:
            return f"http://127.0.0.1:8037{obj.attachment.url}"
        return None

    def validate_attachment(self, value):
        ext = value.name.split('.')[-1].lower()
        if ext not in ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']:
            raise serializers.ValidationError("Only PDF, JPG, PNG, and DOC(X) files are allowed.")
        return value
