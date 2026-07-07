from django.apps import AppConfig


class AttendenceappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendenceapp'

    def ready(self):
        import attendenceapp.signals  # noqa: F401 — register post_save/post_delete handlers
