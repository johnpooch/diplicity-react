from django.contrib import admin
from .models import Order, OrderResolution


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderResolution)
class OrderResolutionAdmin(admin.ModelAdmin):
    pass
