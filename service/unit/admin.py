from django.contrib import admin

from .models import Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["type", "nation", "province", "phase", "dislodged_by"]
    list_filter = ["nation", "province", "phase"]
    search_fields = ["nation", "province", "phase"]
    ordering = ["phase", "nation", "province"]
