from django.apps import AppConfig


class PhaseConfig(AppConfig):
    name = "phase"

    def ready(self):
        import phase.signals  # noqa: F401