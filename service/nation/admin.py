from django.contrib import admin
from .models import Nation


@admin.register(Nation)
class NationAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "variant"]
    list_filter = ["variant"]
    search_fields = ["name"]
    ordering = ["variant", "name"]
