import json
from django.contrib import admin
from django.contrib import messages
from adjudication.service import resolve
from .models import Phase, PhaseState


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ["id", "game", "variant", "ordinal", "season", "year", "type", "status", "scheduled_resolution"]
    list_filter = ["status", "season", "type"]
    search_fields = ["game__name", "season", "year"]
    readonly_fields = ["ordinal", "created_at", "updated_at"]
    actions = ["dry_run_resolution", "revert_to_phase", "show_all_orders"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        """Optimize queryset by selecting related variant."""
        qs = super().get_queryset(request)
        return qs.select_related("variant", "game")

    def dry_run_resolution(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one phase for dry-run resolution.", level=messages.ERROR)
            return

        phase = queryset.first()

        try:
            adjudication_data = resolve(phase)

            formatted_output = json.dumps(adjudication_data, indent=2, default=str)

            self.message_user(
                request, f"Dry-run resolution for {phase.name}:\n\n{formatted_output}", level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(request, f"Error during dry-run resolution: {str(e)}", level=messages.ERROR)

    dry_run_resolution.short_description = "Dry-run resolution (no database changes)"

    def revert_to_phase(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one phase to revert to.", level=messages.ERROR)
            return

        phase = queryset.first()

        try:
            phase.revert_to_this_phase()
            self.message_user(
                request,
                f"Successfully reverted game '{phase.game.name}' to {phase.name}. "
                f"All later phases have been deleted.",
                level=messages.SUCCESS,
            )
        except ValueError as e:
            self.message_user(request, f"Cannot revert phase: {str(e)}", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error reverting phase: {str(e)}", level=messages.ERROR)

    revert_to_phase.short_description = "Revert to this phase"

    def show_all_orders(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one phase to show orders.", level=messages.ERROR)
            return

        phase = queryset.first()

        # Collect all orders from all phase states
        orders_data = []
        for phase_state in phase.phase_states.select_related("member__user", "member__nation").prefetch_related(
            "orders__source", "orders__target", "orders__aux", "orders__named_coast", "orders__resolution"
        ):
            for order in phase_state.orders.all():
                order_dict = {
                    "id": order.id,
                    "nation": phase_state.member.nation.name if phase_state.member.nation else None,
                    "user": phase_state.member.user.username if phase_state.member.user else None,
                    "order_type": order.order_type,
                    "source": order.source.province_id if order.source else None,
                    "source_name": order.source.name if order.source else None,
                    "target": order.target.province_id if order.target else None,
                    "target_name": order.target.name if order.target else None,
                    "aux": order.aux.province_id if order.aux else None,
                    "aux_name": order.aux.name if order.aux else None,
                    "unit_type": order.unit_type,
                    "named_coast": order.named_coast.province_id if order.named_coast else None,
                    "named_coast_name": order.named_coast.name if order.named_coast else None,
                    "complete": order.complete,
                    "title": order.title,
                    "summary": order.summary,
                }

                # Add resolution if it exists
                if hasattr(order, "resolution"):
                    order_dict["resolution"] = {
                        "status": order.resolution.status,
                        "by": order.resolution.by.province_id if order.resolution.by else None,
                        "by_name": order.resolution.by.name if order.resolution.by else None,
                    }

                orders_data.append(order_dict)

        formatted_output = json.dumps(orders_data, indent=2, default=str)

        self.message_user(
            request,
            f"Orders for {phase.name} (Total: {len(orders_data)}):\n\n{formatted_output}",
            level=messages.SUCCESS,
        )

    show_all_orders.short_description = "Show all orders as JSON"


@admin.register(PhaseState)
class PhaseStateAdmin(admin.ModelAdmin):
    list_display = ["id", "phase", "member", "orders_confirmed", "eliminated"]
    list_filter = ["orders_confirmed", "eliminated"]
    search_fields = ["phase__game__name", "member__user__username"]
    readonly_fields = ["created_at", "updated_at"]
