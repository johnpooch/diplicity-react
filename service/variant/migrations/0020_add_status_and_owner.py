from django.conf import settings
from django.db import migrations, models


def backfill_published(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.all().update(status="published")


def backfill_draft(apps, schema_editor):
    Variant = apps.get_model("variant", "Variant")
    Variant.objects.all().update(status="draft")


class Migration(migrations.Migration):

    dependencies = [
        ("variant", "0019_visible_position_markers"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="variant",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("published", "Published"),
                    ("archived", "Archived"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="variant",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="owned_variants",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_published, backfill_draft),
    ]
