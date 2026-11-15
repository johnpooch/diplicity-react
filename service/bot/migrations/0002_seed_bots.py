from django.db import migrations

BOT_EMAIL_DOMAIN = "bots.diplicity.com"
BASIC_ROSTER_SIZE = 40
PREVIOUS_BASIC_ROSTER_SIZE = 8
PROFILE_KIND_TO_BOT_KIND = {"llm": "ai", "dumbbot": "basic"}
NUMERALS = (
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


def roman(number):
    result = ""
    for value, numeral in NUMERALS:
        while number >= value:
            result += numeral
            number -= value
    return result


def automaton_roster():
    return [
        {"name": f"Automaton {roman(n)}", "slug": f"automaton_{roman(n).lower()}"}
        for n in range(1, BASIC_ROSTER_SIZE + 1)
    ]


def seed_bots(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("user_profile", "UserProfile")
    Bot = apps.get_model("bot", "Bot")

    for automaton in automaton_roster():
        user, _ = User.objects.get_or_create(
            email=f"{automaton['slug']}@{BOT_EMAIL_DOMAIN}",
            defaults={"username": f"{automaton['slug']}bot", "is_active": True},
        )
        UserProfile.objects.update_or_create(
            user=user,
            defaults={"name": automaton["name"], "kind": "dumbbot"},
        )

    for profile in UserProfile.objects.filter(kind__in=PROFILE_KIND_TO_BOT_KIND):
        Bot.objects.update_or_create(
            user_id=profile.user_id,
            defaults={
                "kind": PROFILE_KIND_TO_BOT_KIND[profile.kind],
                "name": profile.name,
            },
        )


def remove_bots(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Bot = apps.get_model("bot", "Bot")

    Bot.objects.all().delete()
    User.objects.filter(
        email__in=[
            f"{automaton['slug']}@{BOT_EMAIL_DOMAIN}"
            for automaton in automaton_roster()[PREVIOUS_BASIC_ROSTER_SIZE:]
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bot", "0001_initial"),
        ("user_profile", "0014_remove_userprofile_commitment_from_state"),
    ]

    operations = [
        migrations.RunPython(seed_bots, remove_bots),
    ]
