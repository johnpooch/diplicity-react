import json

from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from lxml.etree import XMLSyntaxError

from common.constants import VariantStatus
from .models import Variant, VariantSvg
from .utils import (
    apply_safe_replacement,
    normalize_dsvg,
    validate_dsvg,
    validate_safe_replacement,
)


class ReplaceVariantFilesForm(forms.Form):
    dvar = forms.FileField(label="DVAR file (JSON)")
    dsvg = forms.FileField(label="DSVG file (SVG)")

    def __init__(self, *args, variant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.variant = variant
        self.parsed_dvar = None
        self.parsed_dsvg = None

    def clean(self):
        cleaned_data = super().clean()
        dvar_upload = cleaned_data.get("dvar")
        dsvg_upload = cleaned_data.get("dsvg")

        if dvar_upload is not None:
            try:
                dvar_text = dvar_upload.read().decode("utf-8")
            except UnicodeDecodeError:
                self.add_error("dvar", "DVAR file is not valid UTF-8.")
            else:
                try:
                    self.parsed_dvar = json.loads(dvar_text)
                except json.JSONDecodeError as exc:
                    self.add_error("dvar", f"DVAR is not valid JSON: {exc}.")

        if dsvg_upload is not None:
            try:
                dsvg_text = dsvg_upload.read().decode("utf-8")
            except UnicodeDecodeError:
                self.add_error("dsvg", "DSVG file is not valid UTF-8.")
            else:
                try:
                    self.parsed_dsvg = normalize_dsvg(dsvg_text)
                except XMLSyntaxError as exc:
                    self.add_error("dsvg", f"DSVG could not be parsed: {exc}.")

        if self.parsed_dvar is not None and self.variant is not None:
            safe_errors = validate_safe_replacement(self.variant, self.parsed_dvar)
            if safe_errors:
                self.add_error(
                    "dvar",
                    [f"{error.code}: {error.message}" for error in safe_errors],
                )

        return cleaned_data


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "official", "owner")
    list_filter = ("status", "official")
    list_editable = ("official",)
    search_fields = ("name", "id")
    autocomplete_fields = ("owner",)
    actions = (
        "publish_selected",
        "archive_selected",
        "revert_to_draft_selected",
        "mark_official_selected",
        "unmark_official_selected",
    )
    change_form_template = "admin/variant/variant/change_form.html"

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

    @admin.action(description="Mark selected as official")
    def mark_official_selected(self, request, queryset):
        updated = queryset.update(official=True)
        self.message_user(request, f"Marked {updated} variant(s) as official.", level=messages.SUCCESS)

    @admin.action(description="Unmark selected as official")
    def unmark_official_selected(self, request, queryset):
        updated = queryset.update(official=False)
        self.message_user(request, f"Unmarked {updated} variant(s).", level=messages.WARNING)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/replace-files/",
                self.admin_site.admin_view(self.replace_files_view),
                name="variant_variant_replace_files",
            ),
        ]
        return custom + urls

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        variant = self.get_object(request, object_id)
        if variant is not None and variant.status == VariantStatus.PUBLISHED:
            extra_context["replace_files_url"] = reverse(
                "admin:variant_variant_replace_files", args=[object_id]
            )
        return super().change_view(request, object_id, form_url, extra_context)

    def replace_files_view(self, request, object_id):
        variant = get_object_or_404(Variant, pk=object_id)

        if variant.status != VariantStatus.PUBLISHED:
            self.message_user(
                request,
                "Safe replacement is only available for published variants.",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse("admin:variant_variant_change", args=[object_id])
            )

        if request.method == "POST":
            form = ReplaceVariantFilesForm(request.POST, request.FILES, variant=variant)
            if form.is_valid():
                dsvg_errors = validate_dsvg(form.parsed_dsvg, variant)
                if dsvg_errors:
                    for error in dsvg_errors:
                        form.add_error("dsvg", f"{error.code}: {error.message}")
                else:
                    with transaction.atomic():
                        apply_safe_replacement(variant, form.parsed_dvar, form.parsed_dsvg)
                    self.message_user(
                        request,
                        f"Replaced files for variant '{variant.id}'.",
                        level=messages.SUCCESS,
                    )
                    return HttpResponseRedirect(
                        reverse("admin:variant_variant_change", args=[object_id])
                    )
        else:
            form = ReplaceVariantFilesForm(variant=variant)

        context = {
            **self.admin_site.each_context(request),
            "title": f"Replace files for {variant.name}",
            "variant": variant,
            "form": form,
            "opts": self.model._meta,
            "original": variant,
        }
        return render(request, "admin/variant/variant/replace_files.html", context)


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
