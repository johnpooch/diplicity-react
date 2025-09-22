from django.contrib import admin
from django.contrib import messages
from .models import (
    Variant,
    Channel,
    ChannelMember,
    ChannelMessage,
    Game,
    Member,
    PhaseState,
    Phase,
    SupplyCenter,
    Unit,
    UserProfile,
)
from .services.game_service import GameService
from .services.adjudication_service import AdjudicationService

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'private', 'created_at')
    list_filter = ('private', 'game')
    search_fields = ('name',)

@admin.register(ChannelMember)
class ChannelMemberAdmin(admin.ModelAdmin):
    list_display = ('member', 'channel', 'created_at')
    list_filter = ('channel',)

@admin.register(ChannelMessage)
class ChannelMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'channel', 'created_at')
    list_filter = ('channel',)
    search_fields = ('body',)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'variant', 'status', 'private', 'movement_phase_duration')
    list_filter = ('status', 'private', 'variant')
    search_fields = ('name', 'id')
    actions = ['start_game', 'resolve_game']

    def start_game(self, request, queryset):
        for game in queryset:
            if game.status != Game.PENDING:
                messages.error(request, f'Game {game.name} is not in pending status')
                continue
            
            try:
                adjudication_service = AdjudicationService(None)
                service = GameService(request.user, adjudication_service)
                service.start(game.id)
                messages.success(request, f'Successfully started game {game.name}')
            except Exception as e:
                messages.error(request, f'Failed to start game {game.name}: {str(e)}')
    
    start_game.short_description = "Start selected games"

    def resolve_game(self, request, queryset):
        for game in queryset:
            if game.status != Game.ACTIVE:
                messages.error(request, f'Game {game.name} is not in active status')
                continue
            
            current_phase = game.current_phase
            if not current_phase:
                messages.error(request, f'Game {game.name} has no current phase')
                continue
                
            if current_phase.status != Phase.ACTIVE:
                messages.error(request, f'Game {game.name} current phase is not active')
                continue
            
            try:
                adjudication_service = AdjudicationService(None)
                service = GameService(request.user, adjudication_service)
                service.resolve(game.id)
                messages.success(request, f'Successfully resolved current phase for game {game.name}')
            except Exception as e:
                messages.error(request, f'Failed to resolve game {game.name}: {str(e)}')
    
    resolve_game.short_description = "Resolve selected games"

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'nation', 'won', 'drew', 'eliminated', 'kicked')
    list_filter = ('game', 'won', 'drew', 'eliminated', 'kicked')
    search_fields = ('user__username', 'nation')


@admin.register(PhaseState)
class PhaseStateAdmin(admin.ModelAdmin):
    list_display = ('member', 'phase', 'orders_confirmed', 'eliminated')
    list_filter = ('orders_confirmed', 'eliminated')

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('game', 'ordinal', 'status', 'season', 'year', 'type')
    list_filter = ('status', 'season', 'type')
    search_fields = ('game__name',)

@admin.register(SupplyCenter)
class SupplyCenterAdmin(admin.ModelAdmin):
    list_display = ('province', 'nation', 'phase')
    list_filter = ('nation',)
    search_fields = ('province',)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('type', 'nation', 'province', 'phase', 'dislodged')
    list_filter = ('type', 'nation', 'dislodged')
    search_fields = ('province',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'email')
    search_fields = ('name', 'user__email', 'user__username')

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
