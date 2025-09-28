from django.db import models
from common.constants import ProvinceType


class Province(models.Model):
    province_id = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ProvinceType.TYPE_CHOICES)
    supply_center = models.BooleanField(default=False)
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, related_name="provinces")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="named_coasts")

    class Meta:
        ordering = ["name"]
        unique_together = ["province_id", "variant"]
