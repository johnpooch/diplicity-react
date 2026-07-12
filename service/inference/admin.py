from django.contrib import admin

from inference.models import Inference


class GameFilter(admin.SimpleListFilter):
    title = "game"
    parameter_name = "game"

    def lookups(self, request, model_admin):
        game_ids = (
            model_admin.get_queryset(request)
            .values_list("phase__game_id", flat=True)
            .distinct()
        )
        return [(game_id, game_id) for game_id in game_ids]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(phase__game_id=self.value())
        return queryset


@admin.register(Inference)
class InferenceAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "nation",
        "channel_nations",
        "phase",
        "status",
        "model",
        "total_tokens",
        "latency_ms",
        "created_at",
    )
    list_filter = ("task", "status", "provider", GameFilter)
    readonly_fields = (
        "task",
        "status",
        "nation",
        "channel_nations",
        "provider",
        "model",
        "game",
        "phase",
        "member",
        "channel",
        "started_at",
        "completed_at",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "total_tokens",
        "created_at",
        "updated_at",
        "system",
        "user_content",
        "response",
        "error_message",
    )
    fieldsets = (
        (
            "Metadata",
            {
                "fields": (
                    "task",
                    "status",
                    "nation",
                    "channel_nations",
                    "provider",
                    "model",
                    "game",
                    "phase",
                    "started_at",
                    "completed_at",
                    "latency_ms",
                    "input_tokens",
                    "output_tokens",
                    "cache_read_tokens",
                    "cache_write_tokens",
                    "total_tokens",
                )
            },
        ),
        ("System", {"fields": ("system",)}),
        ("Input", {"fields": ("user_content",)}),
        ("Output", {"fields": ("response",)}),
        ("Error", {"fields": ("error_message",)}),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("member__nation", "phase")
            .prefetch_related("channel__members__nation")
        )

    def game(self, obj):
        if obj.phase is None:
            return None
        return obj.phase.game_id

    def nation(self, obj):
        if obj.member is None or obj.member.nation is None:
            return None
        return obj.member.nation.name

    def channel_nations(self, obj):
        if obj.channel_id is None:
            return ""
        names = [
            channel_member.nation.name
            for channel_member in obj.channel.members.all()
            if channel_member.id != obj.member_id and channel_member.nation is not None
        ]
        return ", ".join(sorted(names))

    def total_tokens(self, obj):
        return obj.input_tokens + obj.output_tokens
