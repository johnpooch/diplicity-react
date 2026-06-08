from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0015_backfill_game_timestamps'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='confirmation_required',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='game',
            name='confirmation_deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
