import re
import uuid


class SuffixedSlugIdMixin:
    slug_source = None

    def save(self, *args, **kwargs):
        if not self.pk:
            self.pk = self.suffixed_slug(getattr(self, self.slug_source))
            kwargs.setdefault("force_insert", True)
        super().save(*args, **kwargs)

    @staticmethod
    def suffixed_slug(value):
        slug = re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", value.lower()))
        return f"{slug}-{uuid.uuid4().hex[:8]}"
