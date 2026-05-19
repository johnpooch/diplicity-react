import hashlib

from django.db import migrations


def normalize_existing_variant_svgs(apps, schema_editor):
    from variant.utils import normalize_dsvg

    VariantSvg = apps.get_model("variant", "VariantSvg")
    for variant_svg in VariantSvg.objects.all():
        normalized = normalize_dsvg(variant_svg.svg)
        if normalized == variant_svg.svg:
            continue
        variant_svg.svg = normalized
        variant_svg.content_hash = hashlib.sha256(normalized.encode()).hexdigest()
        variant_svg.save(update_fields=["svg", "content_hash"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0016_normalize_variant_svgs"),
    ]

    operations = [
        migrations.RunPython(normalize_existing_variant_svgs, noop_reverse),
    ]
