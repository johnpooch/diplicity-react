from django.contrib import admin

from update.models import Bundle


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display = ["id", "platform", "version", "minimum_native_version", "active", "created_at"]
    list_filter = ["platform", "active", "created_at"]
    search_fields = ["version", "object_key"]
