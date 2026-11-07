from django.contrib import admin
from report.models import Mark, Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        Report.objects.save_report(obj)

    def delete_model(self, request, obj):
        Report.objects.delete_reports(Report.objects.filter(pk=obj.pk))

    def delete_queryset(self, request, queryset):
        Report.objects.delete_reports(queryset)

    list_display = ["id", "reporter", "reported", "reason", "assigned_to", "created_at"]
    list_filter = ["reason", "created_at"]
    raw_id_fields = ["reporter", "reported", "assigned_to"]


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ["id", "member", "reason", "created_at"]
    list_filter = ["reason", "created_at"]
    raw_id_fields = ["member"]
