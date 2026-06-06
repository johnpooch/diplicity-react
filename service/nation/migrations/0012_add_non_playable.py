from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nation", "0011_backfill_bundled_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="nation",
            name="non_playable",
            field=models.BooleanField(default=False),
        ),
    ]
