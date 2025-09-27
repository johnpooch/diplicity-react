from django.contrib import admin
from django.contrib import messages
from .models import Game
from common.constants import PhaseStatus


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "variant", "status", "private", "movement_phase_duration")
    list_filter = ("status", "private", "variant")
    search_fields = ("name", "id")
    actions = ["start_game", "resolve_game"]
