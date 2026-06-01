from django.apps import AppConfig


class PhaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "phase"

    def ready(self):
        import phase.signals  # noqa: F401