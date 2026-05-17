import hashlib
from pathlib import Path

from django.db import migrations

SVG_DIR = Path(__file__).resolve().parent.parent / "data" / "svg"

VARIANT_SVG_FILES = {
    "classical": "classical.d.svg",
    "italy-vs-germany": "classical.d.svg",
    "hundred": "hundred.d.svg",
    "vietnam-war": "vietnam-war.d.svg",
    "canton": "canton.d.svg",
    "youngstown-redux": "youngstown-redux.d.svg",
}


def create_variant_svgs(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    VariantSvg = apps.get_model("variant", "VariantSvg")
    for variant_id, filename in VARIANT_SVG_FILES.items():
        svg = (SVG_DIR / filename).read_text()
        VariantSvg.objects.create(
            variant=Variant.objects.get(id=variant_id),
            svg=svg,
            content_hash=hashlib.sha256(svg.encode()).hexdigest(),
        )


def remove_variant_svgs(apps, schema_editor):
    VariantSvg = apps.get_model("variant", "VariantSvg")
    VariantSvg.objects.filter(variant_id__in=VARIANT_SVG_FILES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('variant', '0013_variantsvg'),
    ]

    operations = [
        migrations.RunPython(create_variant_svgs, remove_variant_svgs),
    ]
