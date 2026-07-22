from django.apps import AppConfig


class EmitConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "emit"

    def ready(self):
        import emit.specs
