# Generated by Django 4.2.21 on 2025-05-23 10:30

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
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=250)),
                ('private', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.CharField(max_length=150, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('private', models.BooleanField(default=False)),
                ('movement_phase_duration', models.CharField(choices=[('24 hours', '24 hours')], default='24 hours', max_length=20)),
                ('nation_assignment', models.CharField(choices=[('random', 'Random'), ('ordered', 'Ordered')], default='random', max_length=20)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nation', models.CharField(blank=True, max_length=100, null=True)),
                ('won', models.BooleanField(default=False)),
                ('drew', models.BooleanField(default=False)),
                ('eliminated', models.BooleanField(default=False)),
                ('kicked', models.BooleanField(default=False)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='game.game')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order_type', models.CharField(max_length=50)),
                ('source', models.CharField(max_length=50)),
                ('target', models.CharField(blank=True, max_length=50, null=True)),
                ('aux', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Phase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ordinal', models.PositiveIntegerField(editable=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('season', models.CharField(max_length=10)),
                ('year', models.IntegerField()),
                ('type', models.CharField(max_length=10)),
                ('remaining_time', models.DurationField(blank=True, null=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phases', to='game.game')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.CharField(editable=False, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('result', models.TextField(blank=True, null=True)),
                ('scheduled_for', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.CharField(max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('picture', models.URLField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(choices=[('fleet', 'Fleet'), ('army', 'Army')], max_length=10)),
                ('nation', models.CharField(max_length=50)),
                ('province', models.CharField(max_length=50)),
                ('dislodged', models.BooleanField(default=False)),
                ('dislodged_by', models.CharField(blank=True, max_length=50, null=True)),
                ('phase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='units', to='game.phase')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupplyCenter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('province', models.CharField(max_length=50)),
                ('nation', models.CharField(max_length=50)),
                ('phase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supply_centers', to='game.phase')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PhaseState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('options', models.TextField(blank=True, null=True)),
                ('orders_confirmed', models.BooleanField(default=False)),
                ('eliminated', models.BooleanField(default=False)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phase_states', to='game.member')),
                ('phase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phase_states', to='game.phase')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderResolution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('OK', 'Succeeded'), ('ErrIllegalMove', 'Illegal move'), ('ErrIllegalDestination', 'Illegal destination'), ('ErrBounce', 'Bounced'), ('ErrInvalidSupporteeOrder', 'Invalid support order'), ('ErrIllegalSupportDestination', 'Illegal support destination'), ('ErrInvalidDestination', 'Invalid destination')], max_length=30)),
                ('by', models.CharField(blank=True, help_text='Province that caused the resolution status (e.g. province that caused a bounce)', max_length=50, null=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='resolution', to='game.order')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='order',
            name='phase_state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='game.phasestate'),
        ),
        migrations.AddField(
            model_name='game',
            name='resolution_task',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='game', to='game.task'),
        ),
        migrations.AddField(
            model_name='game',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='games', to='game.variant'),
        ),
        migrations.CreateModel(
            name='ChannelMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('body', models.TextField()),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='game.channel')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='game.member')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChannelMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='member_channels', to='game.channel')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='member_channels', to='game.member')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='channel',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='game.game'),
        ),
        migrations.AddField(
            model_name='channel',
            name='members',
            field=models.ManyToManyField(related_name='channels', through='game.ChannelMember', to='game.member'),
        ),
    ]
