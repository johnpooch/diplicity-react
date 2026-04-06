from django.db import migrations
from django.utils import timezone


def backfill_public_channel_members(apps, schema_editor):
    Channel = apps.get_model("channel", "Channel")
    ChannelMember = apps.get_model("channel", "ChannelMember")

    now = timezone.now()
    public_channels = Channel.objects.filter(private=False)

    rows_to_create = []
    for channel in public_channels:
        existing_member_ids = set(
            ChannelMember.objects.filter(channel=channel).values_list("member_id", flat=True)
        )
        game_members = channel.game.members.all()
        for member in game_members:
            if member.id not in existing_member_ids:
                rows_to_create.append(
                    ChannelMember(
                        member=member,
                        channel=channel,
                        last_read_at=now,
                    )
                )

    if rows_to_create:
        ChannelMember.objects.bulk_create(rows_to_create, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0002_add_last_read_at_to_channel_member"),
    ]

    operations = [
        migrations.RunPython(
            backfill_public_channel_members,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
