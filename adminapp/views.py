import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, OuterRef, Subquery, IntegerField, F
from django.db.models.functions import TruncDate

from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from coreapp.response import StandardResponseMixin
from authapp.models import Teacher
from studentapp.models import Student
from dashboardapp.models import ActivityLog
from .models import School, AIConfiguration, AIUsageLog
from .serializers import (
    SchoolSerializer, SchoolStatsSerializer, 
    AdminTeacherSerializer, AdminTeacherCreateSerializer, 
    AIConfigurationSerializer, AnalysisReportRequestSerializer
)
from coreapp.ai_utils import call_openai_with_retry, AIServiceError

logger = logging.getLogger("aamyproject")


class AdminLoginView(StandardResponseMixin, APIView):
    """POST /api/admin/login"""
    throttle_scope = "auth"

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")
        
        from django.contrib.auth import authenticate
        user = authenticate(email=email, password=password)
        
        if not user or not user.is_superuser:
            return self.error_response("Invalid credentials or not an admin.", status.HTTP_401_UNAUTHORIZED)
            
        refresh = RefreshToken.for_user(user)
        return self.success_response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {"email": user.email, "first_name": user.first_name, "last_name": user.last_name}
        }, "Admin login successful.")


class AdminDashboardStatsView(StandardResponseMixin, APIView):
    """GET /api/admin/dashboard-stats"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        
        total_teachers = Teacher.objects.count()
        active_schools = School.objects.filter(registration_status="Active").count()
        today_ai_requests = AIUsageLog.objects.filter(created_at__date=today).count()
        
        return self.success_response({
            "total_teachers": total_teachers,
            "active_schools": active_schools,
            "today_ai_requests": today_ai_requests
        }, "Dashboard stats fetched.")


class AdminPlatformUsageView(StandardResponseMixin, APIView):
    """GET /api/admin/platform-usage"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=6)
        
        # Aggregate AI requests per day
        daily_usage = (AIUsageLog.objects
            .filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(requests=Count('log_id'))
            .order_by('date'))
            
        # Fill in missing days with 0
        usage_map = {item['date'].strftime('%A'): item['requests'] for item in daily_usage}
        
        graph_data = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_name = day.strftime('%A')
            graph_data.append({
                "day": day_name,
                "date": day.strftime('%Y-%m-%d'),
                "requests": usage_map.get(day_name, 0)
            })
            
        return self.success_response(graph_data, "Weekly platform usage fetched.")


class AdminTeacherViewSet(StandardResponseMixin, viewsets.ModelViewSet):
    """
    GET /api/admin/teachers
    POST /api/admin/teachers
    """
    permission_classes = [IsAdminUser]
    queryset = Teacher.objects.select_related('school').all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AdminTeacherCreateSerializer
        return AdminTeacherSerializer
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Could not create teacher", status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        teacher = serializer.save()
        return self.success_response(AdminTeacherSerializer(teacher).data, "Teacher created successfully.", status.HTTP_201_CREATED)
        
    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page, many=True)
        return self.success_response(self.get_paginated_response(serializer.data).data, "Teachers fetched.")


class AdminTeacherActivityView(StandardResponseMixin, APIView):
    """GET /api/admin/teachers/{id}/activity"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, pk):
        try:
            teacher = Teacher.objects.select_related('school').get(pk=pk)
        except Teacher.DoesNotExist:
            return self.error_response("Teacher not found", status.HTTP_404_NOT_FOUND)
            
        last_activity = ActivityLog.objects.filter(teacher=teacher).order_by('-created_at').first()
        last_active = last_activity.created_at if last_activity else teacher.updated_at
        
        data = {
            "teacher_name": f"{teacher.first_name} {teacher.last_name}",
            "school_name": teacher.school.school_name if teacher.school else None,
            "last_active": last_active,
            "status": teacher.approval_status
        }
        return self.success_response(data, "Teacher activity fetched.")


class AdminTeacherApproveView(StandardResponseMixin, APIView):
    """POST /api/admin/teachers/{id}/approve"""
    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        try:
            teacher = Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return self.error_response("Teacher not found.", status.HTTP_404_NOT_FOUND)
            
        if teacher.approval_status == "approved":
            return self.error_response("Teacher is already approved.", status.HTTP_400_BAD_REQUEST)
            
        teacher.approval_status = "approved"
        teacher.is_active = True
        teacher.save(update_fields=["approval_status", "is_active", "updated_at"])
        
        return self.success_response(
            AdminTeacherSerializer(teacher).data, 
            "Teacher approved successfully."
        )


from rest_framework.generics import ListAPIView
from rest_framework import serializers

class TeacherActivitySerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    school_name = serializers.CharField(source='school.school_name', read_only=True, allow_null=True)
    last_active = serializers.SerializerMethodField()
    status = serializers.CharField(source='approval_status')

    class Meta:
        model = Teacher
        fields = ['teacher_id', 'teacher_name', 'school_name', 'last_active', 'status']

    def get_teacher_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_last_active(self, obj):
        return getattr(obj, 'last_activity_date', None) or obj.updated_at

class AdminAllTeachersActivityView(StandardResponseMixin, ListAPIView):
    """GET /api/admin/teachers/activity"""
    permission_classes = [IsAdminUser]
    serializer_class = TeacherActivitySerializer
    
    def get_queryset(self):
        latest_activity = ActivityLog.objects.filter(
            teacher=OuterRef('pk')
        ).order_by('-created_at').values('created_at')[:1]
        
        return Teacher.objects.select_related('school').annotate(
            last_activity_date=Subquery(latest_activity)
        ).order_by(F('last_activity_date').desc(nulls_last=True), '-updated_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.success_response(self.get_paginated_response(serializer.data).data, "Teacher activities fetched.")

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(serializer.data, "Teacher activities fetched.")


class AdminSchoolViewSet(StandardResponseMixin, viewsets.ModelViewSet):
    """
    GET /api/admin/schools
    POST /api/admin/schools
    """
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        # Annotate with stats
        teachers_count = Teacher.objects.filter(school=OuterRef('pk')).values('school').annotate(c=Count('teacher_id')).values('c')
        students_count = Student.objects.filter(teacher__school=OuterRef('pk')).values('teacher__school').annotate(c=Count('student_id')).values('c')
        ai_req_count = AIUsageLog.objects.filter(school=OuterRef('pk')).values('school').annotate(c=Count('log_id')).values('c')
        
        return School.objects.annotate(
            total_teachers=Subquery(teachers_count, output_field=IntegerField()),
            total_students=Subquery(students_count, output_field=IntegerField()),
            total_ai_requests=Subquery(ai_req_count, output_field=IntegerField())
        ).order_by('-total_ai_requests')
        
    def get_serializer_class(self):
        if self.action == 'create':
            return SchoolSerializer
        return SchoolStatsSerializer
        
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        
        # Clean nulls from subquery
        for school in qs:
            school.total_teachers = school.total_teachers or 0
            school.total_students = school.total_students or 0
            school.total_ai_requests = school.total_ai_requests or 0
            
        # Check if requesting top schools
        if request.query_params.get("top") == "true":
            qs = qs[:10]
            
        page = self.paginate_queryset(qs) if not request.query_params.get("top") else qs
        serializer = self.get_serializer(page, many=True)
        
        if request.query_params.get("top") == "true":
            return self.success_response(serializer.data, "Top schools fetched.")
        return self.success_response(self.get_paginated_response(serializer.data).data, "Schools fetched.")
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation error", status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        school = serializer.save()
        return self.success_response(SchoolSerializer(school).data, "School created.", status.HTTP_201_CREATED)


class AdminAnalysisReportView(StandardResponseMixin, APIView):
    """POST /api/admin/analysis-report"""
    permission_classes = [IsAdminUser]
    throttle_scope = "ai_generate"
    
    def post(self, request):
        serializer = AnalysisReportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation error", status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
            
        focus = serializer.validated_data["analyticalFocus"]
        school = serializer.validated_data["targetSchoolRange"]
        days = serializer.validated_data["temporalBounds"]
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Gather data for AI prompt
        teacher_count = Teacher.objects.filter(school=school).count()
        student_count = Student.objects.filter(teacher__school=school).count()
        ai_req_count = AIUsageLog.objects.filter(school=school, created_at__gte=start_date).count()
        recent_activities = ActivityLog.objects.filter(teacher__school=school, created_at__gte=start_date).count()
        
        system_prompt = (
            "You are an expert educational data analyst. You will be provided with metrics about a school. "
            "Write a concise, professional analysis report focusing on the provided topic. "
            "Respond ONLY with valid JSON containing a 'report' key with your analysis text."
        )
        
        user_prompt = (
            f"School: {school.school_name}\n"
            f"Topic: {focus}\n"
            f"Timeframe: Last {days} days\n"
            f"Data:\n"
            f"- Total Teachers: {teacher_count}\n"
            f"- Total Students: {student_count}\n"
            f"- AI Feature Usage: {ai_req_count} requests\n"
            f"- General Platform Activities: {recent_activities} events\n"
        )
        
        config = AIConfiguration.get_config()
        
        try:
            parsed = call_openai_with_retry(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=config.ai_model,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            # We log admin AI usage with no specific teacher
            AIUsageLog.objects.create(
                teacher=request.user, # The admin user
                school=school,
                endpoint="analysis_report"
            )
            
            return self.success_response({"report": parsed.get("report", "Report generation failed.")}, "Analysis complete.")
        except AIServiceError as exc:
            return self.error_response(f"AI generation failed: {exc}", status.HTTP_502_BAD_GATEWAY)


class AdminAIConfigView(StandardResponseMixin, APIView):
    """
    GET /api/admin/ai-config
    POST /api/admin/ai-config
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        config = AIConfiguration.get_config()
        return self.success_response(AIConfigurationSerializer(config).data, "AI Configuration fetched.")
        
    def post(self, request):
        config = AIConfiguration.get_config()
        serializer = AIConfigurationSerializer(config, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.error_response("Validation error", status.HTTP_422_UNPROCESSABLE_ENTITY, serializer.errors)
        serializer.save()
        return self.success_response(serializer.data, "AI Configuration updated.")
