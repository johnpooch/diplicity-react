from django.contrib import admin
from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html
from .models import Game
from common.constants import PhaseStatus


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "variant", "status", "current_phase", "view_phases", "private", "movement_phase_duration")
    list_filter = ("status", "private", "variant")
    search_fields = ("name", "id")
    actions = ["start_game", "resolve_game"]

    def get_queryset(self, request):
        """Optimize queryset by prefetching phases for current_phase display."""
        qs = super().get_queryset(request)
        return qs.prefetch_related("phases")

    def current_phase(self, obj):
        """Display the current phase of the game."""
        phase = obj.current_phase
        if phase:
            return f"{phase.name} (#{phase.ordinal})"
        return "-"
    current_phase.short_description = "Current Phase"

    def view_phases(self, obj):
        """Display a link to view all phases for this game."""
        phases = obj.phases.all()
        count = len(phases)
        if count == 0:
            return "-"
        
        url = reverse("admin:phase_phase_changelist") + f"?game__id__exact={obj.id}"
        return format_html('<a href="{}">{} phases</a>', url, count)
    view_phases.short_description = "Phases"
