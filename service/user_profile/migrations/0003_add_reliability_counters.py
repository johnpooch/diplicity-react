from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0002_alter_userprofile_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='games_finished',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='games_abandoned_recent',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
