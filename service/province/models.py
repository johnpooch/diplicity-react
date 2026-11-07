from django.core.cache import cache
from django.db import models
from common.constants import ProvinceType

VARIANT_PROVINCES_CACHE_TIMEOUT = 60 * 60 * 24


class ProvinceManager(models.Manager):
    def cached_for_variant(self, variant):
        key = f"variant-provinces:{variant.id}:{variant.updated_at.isoformat()}"
        provinces = cache.get(key)
        if provinces is None:
            provinces = list(self.filter(variant=variant).select_related("parent"))
            cache.set(key, provinces, VARIANT_PROVINCES_CACHE_TIMEOUT)
        return provinces


class Province(models.Model):
    objects = ProvinceManager()

    province_id = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ProvinceType.TYPE_CHOICES)
    supply_center = models.BooleanField(default=False)
    variant = models.ForeignKey(
        "variant.Variant", on_delete=models.CASCADE, related_name="provinces"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="named_coasts",
    )
    home_nation = models.ForeignKey(
        "nation.Nation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="home_provinces",
    )
    adjacencies = models.JSONField(default=list)

    class Meta:
        ordering = ["name"]
        unique_together = ["province_id", "variant"]

    def __str__(self):
        return f"{self.name} ({self.variant.name})"
