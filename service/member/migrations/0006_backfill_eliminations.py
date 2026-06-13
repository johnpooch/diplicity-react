from django.db import migrations
import logging

logger = logging.getLogger(__name__)


def backfill_eliminations(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    Member = apps.get_model("member", "Member")
    Unit = apps.get_model("unit", "Unit")
    SupplyCenter = apps.get_model("supply_center", "SupplyCenter")
    Phase = apps.get_model("phase", "Phase")

    games = Game.objects.filter(sandbox=False).exclude(
        status__in=["completed", "abandoned"]
    )

    eliminated_count = 0

    for game in games:
        current_phase = (
            Phase.objects.filter(game=game).order_by("-ordinal").first()
        )
        if current_phase is None:
            continue

        nations_with_units = set(
            Unit.objects.filter(phase=current_phase).values_list("nation__name", flat=True)
        )
        nations_with_scs = set(
            SupplyCenter.objects.filter(phase=current_phase).values_list("nation__name", flat=True)
        )
        surviving = nations_with_units | nations_with_scs

        members = Member.objects.filter(
            game=game, eliminated=False, kicked=False
        ).select_related("nation")
        newly_eliminated = [
            m for m in members if m.nation_id and m.nation.name not in surviving
        ]

        if newly_eliminated:
            for m in newly_eliminated:
                m.eliminated = True
            Member.objects.bulk_update(newly_eliminated, ["eliminated"])
            eliminated_count += len(newly_eliminated)
            logger.info(
                f"Backfilled {len(newly_eliminated)} eliminated member(s) in game {game.id}"
            )

    logger.info(f"Elimination backfill complete: {eliminated_count} member(s) flagged")


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0005_member_civil_disorder"),
        ("game", "0012_add_press_type_field"),
        ("phase", "0012_add_canton_template_phase"),
        ("unit", "0009_add_canton_units"),
        ("supply_center", "0007_add_canton_supply_centers"),
    ]

    operations = [
        migrations.RunPython(
            backfill_eliminations,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
