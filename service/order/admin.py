from django.contrib import admin
from .models import Order, OrderResolution


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["phase_state", "order_type", "source", "target", "aux"]


@admin.register(OrderResolution)
class OrderResolutionAdmin(admin.ModelAdmin):
    list_display = ["order", "status", "by"]
