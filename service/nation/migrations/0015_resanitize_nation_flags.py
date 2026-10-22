import hashlib
import logging

from django.db import migrations

from variant.utils import sanitize_svg

logger = logging.getLogger(__name__)


def resanitize_nation_flags(apps, schema_editor):
    NationFlag = apps.get_model("nation", "NationFlag")
    for flag in NationFlag.objects.iterator(chunk_size=50):
        try:
            sanitized = sanitize_svg(flag.svg)
        except ValueError:
            logger.warning("Deleting unsanitizable flag for nation %s", flag.nation_id)
            flag.delete()
            continue
        if sanitized == flag.svg:
            continue
        flag.svg = sanitized
        flag.content_hash = hashlib.sha256(sanitized.encode()).hexdigest()
        flag.save(update_fields=["svg", "content_hash"])


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0014_add_non_playable"),
    ]

    operations = [
        migrations.RunPython(resanitize_nation_flags, migrations.RunPython.noop),
    ]
