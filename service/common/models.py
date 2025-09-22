from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProvinceDisplayMixin:
    def _get_province_display(self, province_id, variant):

        if not hasattr(self, "_province_cache"):
            self._province_cache = {p["id"]: p for p in variant.provinces_data}

        return self._province_cache.get(province_id, None)
