from django.contrib import admin
from .models import Nation


@admin.register(Nation)
class NationAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "variant_name"]
    list_filter = ["variant"]
    search_fields = ["name"]
    ordering = ["variant", "name"]

    def variant_name(self, obj):
        return obj.variant.name if obj.variant else "-"
