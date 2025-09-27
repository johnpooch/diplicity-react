from django.contrib import admin
from django.contrib import messages
from .models import Game
from .services.game_service import GameService
from .services.adjudication_service import AdjudicationService
from common.constants import PhaseStatus


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "variant", "status", "private", "movement_phase_duration")
    list_filter = ("status", "private", "variant")
    search_fields = ("name", "id")
    actions = ["start_game", "resolve_game"]

    def start_game(self, request, queryset):
        for game in queryset:
            if game.status != Game.PENDING:
                messages.error(request, f"Game {game.name} is not in pending status")
                continue

            try:
                adjudication_service = AdjudicationService(None)
                service = GameService(request.user, adjudication_service)
                service.start(game.id)
                messages.success(request, f"Successfully started game {game.name}")
            except Exception as e:
                messages.error(request, f"Failed to start game {game.name}: {str(e)}")

    start_game.short_description = "Start selected games"

    def resolve_game(self, request, queryset):
        for game in queryset:
            if game.status != Game.ACTIVE:
                messages.error(request, f"Game {game.name} is not in active status")
                continue

            current_phase = game.current_phase
            if not current_phase:
                messages.error(request, f"Game {game.name} has no current phase")
                continue

            if current_phase.status != PhaseStatus.ACTIVE:
                messages.error(request, f"Game {game.name} current phase is not active")
                continue

            try:
                adjudication_service = AdjudicationService(None)
                service = GameService(request.user, adjudication_service)
                service.resolve(game.id)
                messages.success(request, f"Successfully resolved current phase for game {game.name}")
            except Exception as e:
                messages.error(request, f"Failed to resolve game {game.name}: {str(e)}")

    resolve_game.short_description = "Resolve selected games"



