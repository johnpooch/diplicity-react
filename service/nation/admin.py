from django import forms
from django.contrib import admin
from lxml import etree

from .models import Nation, NationFlag
from .views import FLAG_MAX_BYTES


@admin.register(Nation)
class NationAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "variant_name"]
    list_filter = ["variant"]
    search_fields = ["name"]
    ordering = ["variant", "name"]

    def variant_name(self, obj):
        return obj.variant.name if obj.variant else "-"


class NationFlagAdminForm(forms.ModelForm):
    svg_file = forms.FileField(required=False, help_text="Upload an SVG flag file.")

    class Meta:
        model = NationFlag
        fields = ["nation"]

    def clean(self):
        cleaned_data = super().clean()
        upload = cleaned_data.get("svg_file")

        if not upload:
            if not self.instance.pk:
                raise forms.ValidationError("Upload an SVG flag file.")
            return cleaned_data

        if upload.size > FLAG_MAX_BYTES:
            raise forms.ValidationError(f"Flag is too large (max {FLAG_MAX_BYTES} bytes).")

        try:
            svg = upload.read().decode("utf-8")
        except UnicodeDecodeError:
            raise forms.ValidationError("Uploaded file is not valid UTF-8 text.")

        try:
            etree.fromstring(svg.encode())
        except etree.XMLSyntaxError as exc:
            raise forms.ValidationError(f"Could not parse SVG: {exc}.")

        self.instance.svg = svg
        return cleaned_data


@admin.register(NationFlag)
class NationFlagAdmin(admin.ModelAdmin):
    form = NationFlagAdminForm
    list_display = ("nation", "variant_name", "content_hash", "updated_at")
    list_filter = ("nation__variant",)
    search_fields = ("nation__name",)
    autocomplete_fields = ("nation",)
    readonly_fields = ("content_hash",)

    def variant_name(self, obj):
        return obj.nation.variant.name if obj.nation else "-"
