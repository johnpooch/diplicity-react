from django.contrib import admin
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "game", "nation_name", "won", "drew", "eliminated", "kicked", "outcome_state")
    list_filter = ("won", "drew", "eliminated", "kicked", "outcome_state")
    search_fields = ("user__username", "game__name")
    raw_id_fields = ("user", "game", "nation")

    def nation_name(self, obj):
        return obj.nation.name if obj.nation else "-"
