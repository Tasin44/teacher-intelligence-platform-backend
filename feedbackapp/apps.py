from django.apps import AppConfig


class FeedbackappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedbackapp'

    def ready(self):
        import feedbackapp.signals  # noqa: F401 — register post_save/post_delete handlers
