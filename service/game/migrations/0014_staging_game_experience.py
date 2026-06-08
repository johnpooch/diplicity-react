from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0013_delete_empty_pending_games'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='confirmation_required',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='game',
            name='confirmation_deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
