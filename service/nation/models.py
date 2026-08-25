import hashlib

from django.db import models
from django.urls import reverse

from common.models import BaseModel


class Nation(models.Model):
    nation_id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7)
    non_playable = models.BooleanField(default=False)
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, related_name="nations")

    class Meta:
        ordering = ["name"]
        unique_together = [["name", "variant"], ["nation_id", "variant"]]

    @property
    def flag_path(self) -> str | None:
        try:
            flag = self.flag
        except NationFlag.DoesNotExist:
            return None
        return reverse(
            "nation-flag-svg",
            kwargs={
                "variant_id": self.variant_id,
                "nation_id": self.nation_id,
                "content_hash": flag.content_hash,
            },
        )

    def __str__(self):
        return f"{self.name} ({self.variant.name})"


class NationFlag(BaseModel):
    nation = models.OneToOneField(Nation, on_delete=models.CASCADE, related_name="flag")
    svg = models.TextField()
    content_hash = models.CharField(max_length=64, editable=False)

    def save(self, *args, **kwargs):
        from variant.utils import sanitize_svg

        self.svg = sanitize_svg(self.svg)
        self.content_hash = hashlib.sha256(self.svg.encode()).hexdigest()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"svg", "content_hash"}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nation} flag"
