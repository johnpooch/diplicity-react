from django.contrib import admin
from .models import Province


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "supply_center", "variant"]
    list_filter = ["type", "supply_center", "variant"]
    search_fields = ["id", "name"]
    ordering = ["variant", "name"]
