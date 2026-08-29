from django.conf import settings
from django.db import models

from common.constants import BundlePlatform
from common.models import BaseModel
from update.utils import parse_version


class BundleManager(models.Manager):
    def latest_for(self, platform, native_version):
        runnable = [
            bundle
            for bundle in self.filter(platform=platform, active=True)
            if parse_version(bundle.minimum_native_version) <= parse_version(native_version)
        ]
        if not runnable:
            return None
        return max(runnable, key=lambda bundle: parse_version(bundle.version))


class Bundle(BaseModel):
    objects = BundleManager()

    version = models.CharField(max_length=32)
    platform = models.CharField(max_length=16, choices=BundlePlatform.PLATFORM_CHOICES)
    checksum = models.CharField(max_length=64, blank=True)
    object_key = models.CharField(max_length=255)
    minimum_native_version = models.CharField(max_length=32)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [["platform", "version"]]
        indexes = [
            models.Index(fields=["platform", "active"]),
        ]

    @property
    def url(self):
        return f"{settings.R2_PUBLIC_BASE_URL.rstrip('/')}/{self.object_key}"
