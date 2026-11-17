from django.contrib import admin

from bot.models import Bot, Run


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "user")
    list_filter = ("kind",)
    search_fields = ("name",)


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = ("step", "status", "bot", "phase", "created_at", "completed_at")
    list_filter = ("step", "status")
    raw_id_fields = ("member", "phase", "draw_proposal")
