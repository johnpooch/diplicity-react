from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0013_delete_empty_pending_games"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="game",
            name="finished_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
