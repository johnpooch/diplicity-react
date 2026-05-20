from django import forms
from django.contrib import admin, messages
from lxml.etree import XMLSyntaxError

from common.constants import VariantStatus
from .models import Variant, VariantSvg
from .utils import normalize_dsvg, validate_dsvg


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "owner")
    list_filter = ("status",)
    search_fields = ("name", "id")
    autocomplete_fields = ("owner",)
    actions = ("publish_selected", "archive_selected", "revert_to_draft_selected")

    @admin.action(description="Publish selected drafts")
    def publish_selected(self, request, queryset):
        updated = queryset.filter(status=VariantStatus.DRAFT).update(status=VariantStatus.PUBLISHED)
        self.message_user(request, f"Published {updated} variant(s).", level=messages.SUCCESS)

    @admin.action(description="Archive selected published variants")
    def archive_selected(self, request, queryset):
        updated = queryset.filter(status=VariantStatus.PUBLISHED).update(status=VariantStatus.ARCHIVED)
        self.message_user(request, f"Archived {updated} variant(s).", level=messages.SUCCESS)

    @admin.action(description="Revert selected to draft (use with care)")
    def revert_to_draft_selected(self, request, queryset):
        updated = queryset.exclude(status=VariantStatus.DRAFT).update(status=VariantStatus.DRAFT)
        self.message_user(request, f"Reverted {updated} variant(s) to draft.", level=messages.WARNING)


class VariantSvgAdminForm(forms.ModelForm):
    svg_file = forms.FileField(required=False, help_text="Upload a dSVG file.")

    class Meta:
        model = VariantSvg
        fields = ["variant"]

    def clean(self):
        cleaned_data = super().clean()
        upload = cleaned_data.get("svg_file")

        if not upload:
            if not self.instance.pk:
                raise forms.ValidationError("Upload a dSVG file.")
            return cleaned_data

        try:
            svg = upload.read().decode()
        except UnicodeDecodeError:
            raise forms.ValidationError("Uploaded file is not valid UTF-8 text.")

        try:
            svg = normalize_dsvg(svg)
        except XMLSyntaxError as exc:
            raise forms.ValidationError(f"Could not parse SVG: {exc}.")

        errors = validate_dsvg(svg, cleaned_data.get("variant"))
        if errors:
            raise forms.ValidationError([f"{error.code}: {error.message}" for error in errors])

        self.instance.svg = svg
        return cleaned_data


@admin.register(VariantSvg)
class VariantSvgAdmin(admin.ModelAdmin):
    form = VariantSvgAdminForm
    list_display = ("variant", "content_hash", "updated_at")
    readonly_fields = ("content_hash",)
