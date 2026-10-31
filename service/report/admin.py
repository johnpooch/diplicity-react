from django.contrib import admin
from report.models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["id", "game", "reporter", "reported_user", "reason", "created_at"]
    list_filter = ["reason", "created_at"]
    raw_id_fields = ["game", "reporter", "reported_member", "reported_user"]
