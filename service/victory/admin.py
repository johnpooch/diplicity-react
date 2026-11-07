from django.contrib import admin
from victory.models import Victory


@admin.register(Victory)
class VictoryAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        Victory.objects.save_victory(obj)

    def delete_model(self, request, obj):
        Victory.objects.delete_victories(Victory.objects.filter(pk=obj.pk))

    def delete_queryset(self, request, queryset):
        Victory.objects.delete_victories(queryset)

    list_display = ["id", "game", "type", "winning_phase", "created_at"]
    list_filter = ["created_at"]
    raw_id_fields = ["game", "winning_phase"]
    filter_horizontal = ["members"]
