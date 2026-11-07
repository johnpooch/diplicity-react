from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("game", "0028_game_ranked")]

    operations = [
        migrations.AddField(
            model_name="game",
            name="version",
            field=models.PositiveBigIntegerField(
                db_default=0, default=0, editable=False
            ),
        ),
        migrations.RunSQL("UPDATE game_game SET version = 1", migrations.RunSQL.noop),
    ]
