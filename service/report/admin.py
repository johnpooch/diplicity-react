from django.contrib import admin
from report.models import Mark, Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["id", "reporter", "reported", "reason", "assigned_to", "created_at"]
    list_filter = ["reason", "created_at"]
    raw_id_fields = ["reporter", "reported", "assigned_to"]


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ["id", "member", "reason", "created_at"]
    list_filter = ["reason", "created_at"]
    raw_id_fields = ["member"]
