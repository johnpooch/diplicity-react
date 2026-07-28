from django.contrib import admin

from agent.models import AgentTask


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = (
        "kind",
        "status",
        "member",
        "phase",
        "channel",
        "attempts",
        "created_at",
    )
    list_filter = ("kind", "status")
    readonly_fields = (
        "attempts",
        "last_error",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    )
