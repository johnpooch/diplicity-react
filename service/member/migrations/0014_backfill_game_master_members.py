from django.db import migrations


def seat_existing_game_masters(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    Member = apps.get_model("member", "Member")
    Channel = apps.get_model("channel", "Channel")
    ChannelMember = apps.get_model("channel", "ChannelMember")

    seated_game_ids = set(
        Member.objects.filter(kind="game_master").values_list("game_id", flat=True)
    )

    for game in Game.objects.filter(game_master__isnull=False).exclude(id__in=seated_game_ids):
        if Member.objects.filter(game=game, user_id=game.game_master_id).exists():
            continue

        member = Member.objects.create(game=game, user_id=game.game_master_id, kind="game_master")

        public_channel = Channel.objects.filter(game=game, private=False).first()
        if public_channel is not None:
            ChannelMember.objects.create(member=member, channel=public_channel)


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0013_member_kind_and_more"),
        ("channel", "0006_widen_channel_name"),
    ]

    operations = [
        migrations.RunPython(seat_existing_game_masters, migrations.RunPython.noop),
    ]
