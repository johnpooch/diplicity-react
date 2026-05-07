from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0012_add_press_type_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='min_reliability',
            field=models.CharField(
                choices=[
                    ('open', 'Open'),
                    ('reliable_and_new', 'Reliable + New Players'),
                    ('reliable_only', 'Reliable only'),
                ],
                default='open',
                max_length=20,
            ),
        ),
    ]
