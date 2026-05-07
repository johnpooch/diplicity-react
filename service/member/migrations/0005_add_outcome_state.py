from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0004_make_user_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='outcome_state',
            field=models.CharField(
                blank=True,
                choices=[('completed', 'Completed'), ('abandoned', 'Abandoned')],
                max_length=20,
                null=True,
            ),
        ),
    ]
