from rest_framework.permissions import BasePermission


class IsOwnerTeacher(BasePermission):
    """
    Object-level permission: only the teacher who owns a row (directly via
    `teacher` FK, or indirectly via `student.teacher`) may read/write it.
    Prevents cross-tenant data leaks between teachers.
    """

    def has_object_permission(self, request, view, obj):
        teacher_id = getattr(obj, "teacher_id", None)
        if teacher_id is None and hasattr(obj, "student"):
            teacher_id = obj.student.teacher_id
        return teacher_id == request.user.id
