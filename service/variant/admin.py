from django import forms
from django.contrib import admin
from lxml.etree import XMLSyntaxError

from .models import Variant, VariantSvg
from .utils import normalize_dsvg, validate_dsvg


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


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
