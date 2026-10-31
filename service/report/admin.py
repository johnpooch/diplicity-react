from django.contrib import admin
from report.models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["id", "reporter", "reported", "reason", "created_at"]
    list_filter = ["reason", "created_at"]
    raw_id_fields = ["reporter", "reported"]
