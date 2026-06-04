from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phase', '0013_phasestate_deadline_warning_sent_for'),
    ]

    operations = [
        migrations.AddField(
            model_name='phasestate',
            name='orders_outcome',
            field=models.CharField(
                blank=True,
                choices=[('received', 'Received'), ('nmr', 'Nmr')],
                default=None,
                max_length=8,
                null=True,
            ),
        ),
    ]
