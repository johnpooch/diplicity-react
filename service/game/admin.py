from django.contrib import admin

from .models import Variant
from .models import Task

admin.site.register(Variant)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at", "updated_at", "result")
    list_filter = ("status",)
