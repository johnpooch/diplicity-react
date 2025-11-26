from django.contrib import admin

from .models import Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["type", "nation", "province", "phase", "dislodged_by"]
    list_filter = ["nation", "province", "phase"]
    search_fields = ["nation", "province", "phase"]
    ordering = ["phase", "nation", "province"]

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
            "dislodged_by",
            "dislodged_by__nation",
            "dislodged_by__province",
        )
