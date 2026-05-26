import hashlib
from pathlib import Path

from django.db import migrations


FLAGS_DIR = Path(__file__).resolve().parent.parent.parent / "variant" / "data" / "flags"
BUNDLED_VARIANT_IDS = ["classical", "canton", "vietnam-war", "italy-vs-germany"]


def backfill(apps, schema_editor):
    from variant.utils import sanitize_svg

    Nation = apps.get_model("nation", "Nation")
    NationFlag = apps.get_model("nation", "NationFlag")

    for variant_dir in sorted(FLAGS_DIR.iterdir()):
        if not variant_dir.is_dir():
            continue
        variant_id = variant_dir.name
        nations = {
            nation.nation_id: nation
            for nation in Nation.objects.filter(variant_id=variant_id)
        }
        for svg_file in sorted(variant_dir.glob("*.svg")):
            nation = nations.get(svg_file.stem)
            if nation is None:
                continue
            svg = sanitize_svg(svg_file.read_text())
            NationFlag.objects.update_or_create(
                nation=nation,
                defaults={
                    "svg": svg,
                    "content_hash": hashlib.sha256(svg.encode()).hexdigest(),
                },
            )


def reverse(apps, schema_editor):
    NationFlag = apps.get_model("nation", "NationFlag")
    NationFlag.objects.filter(nation__variant_id__in=BUNDLED_VARIANT_IDS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0010_nationflag"),
        ("variant", "0020_add_status_and_owner"),
    ]

    operations = [
        migrations.RunPython(backfill, reverse),
    ]
