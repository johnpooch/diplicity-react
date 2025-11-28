from django.contrib import admin
from victory.models import Victory


@admin.register(Victory)
class VictoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'game', 'type', 'winning_phase', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['game', 'winning_phase']
    filter_horizontal = ['members']
