from django.contrib import admin
from rating.models import NationHandicap


@admin.register(NationHandicap)
class NationHandicapAdmin(admin.ModelAdmin):
    list_display = ["id", "nation", "offset", "updated_at"]
    list_filter = ["nation__variant"]
    search_fields = ["nation__name"]
    autocomplete_fields = ["nation"]
