import hashlib
import logging

from django.db import migrations

from variant.utils import sanitize_svg

logger = logging.getLogger(__name__)


def resanitize_variant_svgs(apps, schema_editor):
    VariantSvg = apps.get_model("variant", "VariantSvg")
    for variant_svg in VariantSvg.objects.iterator(chunk_size=10):
        try:
            sanitized = sanitize_svg(variant_svg.svg)
        except ValueError:
            logger.warning("Deleting unsanitizable SVG for variant %s", variant_svg.variant_id)
            variant_svg.delete()
            continue
        if sanitized == variant_svg.svg:
            continue
        logger.warning("Re-sanitized SVG for variant %s", variant_svg.variant_id)
        variant_svg.svg = sanitized
        variant_svg.content_hash = hashlib.sha256(sanitized.encode()).hexdigest()
        variant_svg.save(update_fields=["svg", "content_hash"])


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0025_variant_unit_scaling"),
    ]

    operations = [
        migrations.RunPython(resanitize_variant_svgs, migrations.RunPython.noop),
    ]
