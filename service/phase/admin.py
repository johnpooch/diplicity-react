from django.contrib import admin
from .models import Phase, PhaseState


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'game', 'ordinal', 'season', 'year', 'type', 'status', 'scheduled_resolution']
    list_filter = ['status', 'season', 'type']
    search_fields = ['game__name', 'season', 'year']
    readonly_fields = ['ordinal', 'created_at', 'updated_at']


@admin.register(PhaseState)
class PhaseStateAdmin(admin.ModelAdmin):
    list_display = ['id', 'phase', 'member', 'orders_confirmed', 'eliminated']
    list_filter = ['orders_confirmed', 'eliminated']
    search_fields = ['phase__game__name', 'member__user__username']
    readonly_fields = ['created_at', 'updated_at']