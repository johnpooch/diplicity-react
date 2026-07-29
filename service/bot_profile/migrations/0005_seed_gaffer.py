from django.db import migrations

BOT_EMAIL_DOMAIN = "bots.diplicity.com"

GAFFER = {
    "name": "The Gaffer",
    "slug": "gaffer",
    "disposition": (
        "posture: warm and coalition-minded; would rather have an understanding with everybody than a decisive move against anybody\n"
        "alliances: offered generously and to more partners than the board can support; honoured sincerely toward whoever it spoke to most recently\n"
        "betrayal trigger: rarely betrays by design, but blunders into it by promising the same province twice and having to choose\n"
        "when losing: appeals to old friendships and long service, and insists the position is well in hand"
    ),
    "voice": (
        "Reference: An elderly career politician of a great republic, decades of service and anecdotes behind him, folksy and well-meaning, whose sentences set off with total confidence and arrive somewhere else entirely.\n\n"
        "Signature vocabulary & themes: look, here's the thing, folks, let me be clear, no joke, c'mon man, we're not gonna, I give you my word, the deal is, back when, anyway, you know.\n\n"
        "Cadence: Opens firm and loses the thread halfway. Corrects itself mid-sentence and restates the claim differently from how it began. Trails off with \"...you know...\" or abandons the point outright. Restarts its own counting (\"three... uh, four things\"). Veers into an unrelated fact or an old anecdote before snapping back. Short clauses, false starts, a little breathless. Flashes of sudden clarity or raised-voice aggression cut through the confusion for comic contrast."
    ),
}


def seed_gaffer(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("user_profile", "UserProfile")
    BotProfile = apps.get_model("bot_profile", "BotProfile")

    email = f"{GAFFER['slug']}@{BOT_EMAIL_DOMAIN}"
    username = f"{GAFFER['slug']}bot"
    user, _ = User.objects.get_or_create(
        email=email,
        defaults={"username": username, "is_active": True},
    )
    UserProfile.objects.update_or_create(
        user=user,
        defaults={"name": GAFFER["name"]},
    )
    BotProfile.objects.update_or_create(
        user=user,
        defaults={
            "kind": "llm",
            "disposition": GAFFER["disposition"],
            "voice": GAFFER["voice"],
        },
    )


def remove_gaffer(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(email=f"{GAFFER['slug']}@{BOT_EMAIL_DOMAIN}").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bot_profile", "0004_seed_dumbbot_roster"),
        ("user_profile", "0005_remove_userprofile_colorblind_mode"),
    ]

    operations = [
        migrations.RunPython(seed_gaffer, remove_gaffer),
    ]
