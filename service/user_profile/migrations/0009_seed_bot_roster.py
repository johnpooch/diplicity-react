from django.db import migrations

BOT_EMAIL_DOMAIN = "bots.diplicity.com"
LEGACY_BOT_USERNAME = "diplicitybot"

ROSTER = [
    {"name": "The Dealmaker", "slug": "dealmaker", "kind": "llm"},
    {"name": "The Iron Lady", "slug": "iron_lady", "kind": "llm"},
    {"name": "The Bear", "slug": "bear", "kind": "llm"},
    {"name": "The Chairman", "slug": "chairman", "kind": "llm"},
    {"name": "The Eagle", "slug": "eagle", "kind": "llm"},
    {"name": "The Sultan", "slug": "sultan", "kind": "llm"},
    {"name": "The Revolutionary", "slug": "revolutionary", "kind": "llm"},
    {"name": "The Commissar", "slug": "commissar", "kind": "llm"},
    {"name": "The Sun God", "slug": "sun_god", "kind": "llm"},
    {"name": "The Shogun", "slug": "shogun", "kind": "llm"},
    {"name": "The Imperator", "slug": "imperator", "kind": "llm"},
    {"name": "The Viceroy", "slug": "viceroy", "kind": "llm"},
    {"name": "The Gaffer", "slug": "gaffer", "kind": "llm"},
    {"name": "Automaton I", "slug": "automaton_i", "kind": "dumbbot"},
    {"name": "Automaton II", "slug": "automaton_ii", "kind": "dumbbot"},
    {"name": "Automaton III", "slug": "automaton_iii", "kind": "dumbbot"},
    {"name": "Automaton IV", "slug": "automaton_iv", "kind": "dumbbot"},
    {"name": "Automaton V", "slug": "automaton_v", "kind": "dumbbot"},
    {"name": "Automaton VI", "slug": "automaton_vi", "kind": "dumbbot"},
    {"name": "Automaton VII", "slug": "automaton_vii", "kind": "dumbbot"},
    {"name": "Automaton VIII", "slug": "automaton_viii", "kind": "dumbbot"},
]


def seed_roster(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("user_profile", "UserProfile")

    User.objects.filter(username=LEGACY_BOT_USERNAME).delete()

    for bot in ROSTER:
        user, _ = User.objects.get_or_create(
            email=f"{bot['slug']}@{BOT_EMAIL_DOMAIN}",
            defaults={"username": f"{bot['slug']}bot", "is_active": True},
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={"name": bot["name"], "kind": bot["kind"]},
        )


def remove_roster(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(email__in=[f"{bot['slug']}@{BOT_EMAIL_DOMAIN}" for bot in ROSTER]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("user_profile", "0008_drop_bot_profile"),
    ]

    operations = [
        migrations.RunPython(seed_roster, remove_roster),
    ]
