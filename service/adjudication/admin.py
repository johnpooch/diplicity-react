from django.contrib import admin

from .models import ShadowAdjudicationDiff


@admin.register(ShadowAdjudicationDiff)
class ShadowAdjudicationDiffAdmin(admin.ModelAdmin):
    list_display = ["id", "phase", "tier", "created_at"]
    list_filter = ["tier", "created_at"]
    search_fields = ["phase__game__name"]
    raw_id_fields = ["phase"]
    ordering = ["-created_at"]
    readonly_fields = [
        "phase",
        "tier",
        "pre_state",
        "godip_response",
        "python_response",
        "diff_summary",
        "created_at",
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("phase", "phase__game")
