from django.contrib import admin
from .models import Province


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "supply_center", "variant_name"]
    list_filter = ["type", "supply_center", "variant"]
    search_fields = ["id", "name"]
    ordering = ["variant", "name"]

    def variant_name(self, obj):
        return obj.variant.name if obj.variant else "-"
