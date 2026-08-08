from django.contrib import admin

from harness.models import EvalRun, EvalScore


class EvalScoreInline(admin.TabularInline):
    model = EvalScore
    extra = 0
    readonly_fields = ("scorer", "metric", "value", "stderr", "sample_count")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EvalRun)
class EvalRunAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "model", "commit", "dataset", "epochs", "ran_at")
    list_filter = ("kind", "model")
    readonly_fields = (
        "kind",
        "model",
        "commit",
        "dataset",
        "epochs",
        "eval_id",
        "ran_at",
        "created_at",
        "updated_at",
    )
    inlines = (EvalScoreInline,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("scores")
