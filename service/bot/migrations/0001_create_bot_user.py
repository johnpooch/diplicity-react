from django.db import migrations

BOT_USER_EMAIL = "bot@diplicity.com"
BOT_USER_USERNAME = "diplicitybot"
BOT_USER_NAME = "Diplicity Bot"


def create_bot_user(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("user_profile", "UserProfile")

    user, _ = User.objects.get_or_create(
        email=BOT_USER_EMAIL,
        defaults={"username": BOT_USER_USERNAME, "is_active": True},
    )
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"name": BOT_USER_NAME},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("user_profile", "0004_add_colorblind_mode"),
    ]

    operations = [
        migrations.RunPython(create_bot_user, migrations.RunPython.noop),
    ]
