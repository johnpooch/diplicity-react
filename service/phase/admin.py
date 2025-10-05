import json
from django.contrib import admin
from django.contrib import messages
from adjudication.service import resolve
from .models import Phase, PhaseState


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ["id", "game", "ordinal", "season", "year", "type", "status", "scheduled_resolution"]
    list_filter = ["status", "season", "type"]
    search_fields = ["game__name", "season", "year"]
    readonly_fields = ["ordinal", "created_at", "updated_at"]
    actions = ["dry_run_resolution"]
    ordering = ["-created_at"]

    def dry_run_resolution(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly one phase for dry-run resolution.",
                level=messages.ERROR
            )
            return

        phase = queryset.first()

        try:
            adjudication_data = resolve(phase)

            formatted_output = json.dumps(adjudication_data, indent=2, default=str)

            self.message_user(
                request,
                f"Dry-run resolution for {phase.name}:\n\n{formatted_output}",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f"Error during dry-run resolution: {str(e)}",
                level=messages.ERROR
            )

    dry_run_resolution.short_description = "Dry-run resolution (no database changes)"


@admin.register(PhaseState)
class PhaseStateAdmin(admin.ModelAdmin):
    list_display = ["id", "phase", "member", "orders_confirmed", "eliminated"]
    list_filter = ["orders_confirmed", "eliminated"]
    search_fields = ["phase__game__name", "member__user__username"]
    readonly_fields = ["created_at", "updated_at"]
