from django.contrib import admin
from .models import Order, OrderResolution


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["phase_state", "order_type", "source_name", "target_name", "aux_name"]

    def source_name(self, obj):
        return obj.source.name if obj.source else "-"

    source_name.short_description = "Source"
    source_name.admin_order_field = "source__name"

    def target_name(self, obj):
        return obj.target.name if obj.target else "-"

    target_name.short_description = "Target"
    target_name.admin_order_field = "target__name"

    def aux_name(self, obj):
        return obj.aux.name if obj.aux else "-"

    aux_name.short_description = "Aux"
    aux_name.admin_order_field = "aux__name"


@admin.register(OrderResolution)
class OrderResolutionAdmin(admin.ModelAdmin):
    list_display = ["order", "status", "by"]
