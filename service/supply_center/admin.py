from django.contrib import admin
from .models import SupplyCenter


@admin.register(SupplyCenter)
class SupplyCenterAdmin(admin.ModelAdmin):
    list_display = ["province", "nation", "phase"]
    list_filter = []
    search_fields = ["province__name", "nation__name", "phase__game__name"]
    raw_id_fields = ["province", "nation", "phase"]
    ordering = ["phase", "province", "nation"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "nation",
            "nation__variant",
            "province",
            "province__variant",
            "province__parent",
            "phase",
            "phase__game",
            "phase__variant",
        )
