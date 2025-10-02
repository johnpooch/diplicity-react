from django.db import models


class Nation(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7)
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, related_name="nations")

    class Meta:
        ordering = ["name"]
        unique_together = ["name", "variant"]

    def __str__(self):
        return f"{self.name} ({self.variant.name})"
