import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

BOT_USER_EMAIL = "bot@diplicity.com"
BOT_DISPOSITION = "Balanced and pragmatic; willing to ally or betray as the board demands."
BOT_VOICE = "Plain and direct."


def create_bot_profile(apps, schema_editor):
    User = apps.get_model("auth", "User")
    BotProfile = apps.get_model("bot", "BotProfile")

    user = User.objects.filter(email=BOT_USER_EMAIL).first()
    if user is None:
        return
    BotProfile.objects.get_or_create(
        user=user,
        defaults={"disposition": BOT_DISPOSITION, "voice": BOT_VOICE},
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("bot", "0001_create_bot_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BotProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("disposition", models.TextField()),
                ("voice", models.TextField()),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bot_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.RunPython(create_bot_profile, migrations.RunPython.noop),
    ]
