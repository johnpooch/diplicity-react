from django.apps import AppConfig


class EmitConfig(AppConfig):
    name = "emit"

    def ready(self):
        import agent.registry
        import channel.registry
        import discord_service.registry
        import notification.registry
