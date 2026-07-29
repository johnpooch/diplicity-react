from django.db import migrations

BOT_EMAIL_DOMAIN = "bots.diplicity.com"

DUMBBOT_ROSTER = [
    {"name": "Automaton I", "slug": "automaton_i"},
    {"name": "Automaton II", "slug": "automaton_ii"},
    {"name": "Automaton III", "slug": "automaton_iii"},
    {"name": "Automaton IV", "slug": "automaton_iv"},
    {"name": "Automaton V", "slug": "automaton_v"},
    {"name": "Automaton VI", "slug": "automaton_vi"},
    {"name": "Automaton VII", "slug": "automaton_vii"},
    {"name": "Automaton VIII", "slug": "automaton_viii"},
]


def seed_dumbbot_roster(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("user_profile", "UserProfile")
    BotProfile = apps.get_model("bot_profile", "BotProfile")

    for bot in DUMBBOT_ROSTER:
        email = f"{bot['slug']}@{BOT_EMAIL_DOMAIN}"
        username = f"{bot['slug']}bot"
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "is_active": True},
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={"name": bot["name"]},
        )
        BotProfile.objects.update_or_create(
            user=user,
            defaults={
                "kind": "dumbbot",
                "disposition": "",
                "voice": "",
            },
        )


def remove_dumbbot_roster(apps, schema_editor):
    User = apps.get_model("auth", "User")
    emails = [f"{bot['slug']}@{BOT_EMAIL_DOMAIN}" for bot in DUMBBOT_ROSTER]
    User.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bot_profile", "0003_botprofile_kind"),
        ("user_profile", "0005_remove_userprofile_colorblind_mode"),
    ]

    operations = [
        migrations.RunPython(seed_dumbbot_roster, remove_dumbbot_roster),
    ]
