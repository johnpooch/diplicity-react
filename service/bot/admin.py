from django.contrib import admin

from bot.models import Bot


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "user")
    list_filter = ("kind",)
    search_fields = ("name",)
