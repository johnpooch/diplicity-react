from django.contrib import admin
from .models import SupplyCenter


@admin.register(SupplyCenter)
class SupplyCenterAdmin(admin.ModelAdmin):
    list_display = ["province", "nation", "phase"]
    list_filter = ["nation", "phase"]
    search_fields = ["province", "nation"]
    ordering = ["phase", "province", "nation"]
