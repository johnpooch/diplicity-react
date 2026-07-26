from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event_type', models.CharField(max_length=100)),
                ('recipient', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NotificationDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('channel', models.CharField(choices=[('push', 'Push'), ('email', 'Email')], max_length=20)),
                ('heading', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('link', models.CharField(blank=True, max_length=500, null=True)),
                ('data', models.JSONField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('error', models.TextField(blank=True, null=True)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='notification.notification')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
