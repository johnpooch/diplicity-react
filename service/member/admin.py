from django.contrib import admin
from django.contrib import messages

from agent.replan import ReplanError, replan
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "game", "nation_name", "won", "drew", "eliminated", "kicked")
    list_filter = ("won", "drew", "eliminated", "kicked")
    search_fields = ("user__username", "game__name")
    raw_id_fields = ("user", "game", "nation")
    actions = ["replan_orders"]

    def nation_name(self, obj):
        return obj.nation.name if obj.nation else "-"

    def replan_orders(self, request, queryset):
        for member in queryset.select_related("game", "nation", "user"):
            try:
                replan(member)
            except ReplanError as e:
                self.message_user(request, str(e), level=messages.ERROR)
            else:
                self.message_user(request, f"Queued a re-plan for {member}.", level=messages.SUCCESS)

    replan_orders.short_description = "Re-plan orders (bot members only)"
