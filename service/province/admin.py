from django.contrib import admin
from variant.models import Variant
from .models import Province


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "supply_center", "variant_name"]
    list_filter = ["type", "supply_center", "variant"]
    search_fields = ["id", "name"]
    ordering = ["variant", "name"]

    def variant_name(self, obj):
        return obj.variant.name if obj.variant else "-"

    def save_model(self, request, obj, form, change):
        variant_ids = {obj.variant_id}
        if change:
            variant_ids.add(
                Province.objects.values_list("variant_id", flat=True).get(pk=obj.pk)
            )
        super().save_model(request, obj, form, change)
        for variant in Variant.objects.filter(pk__in=variant_ids):
            variant.save()

    def delete_model(self, request, obj):
        variant = obj.variant
        super().delete_model(request, obj)
        variant.save()

    def delete_queryset(self, request, queryset):
        variants = list(Variant.objects.filter(provinces__in=queryset).distinct())
        super().delete_queryset(request, queryset)
        for variant in variants:
            variant.save()
