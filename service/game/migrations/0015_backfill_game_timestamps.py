from django.db import migrations


CHUNK_SIZE = 500


def backfill_finished_at(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    total = 0
    while True:
        ids = list(
            Game.objects.filter(
                status__in=["completed", "abandoned"],
                finished_at__isnull=True,
            ).values_list("id", flat=True)[:CHUNK_SIZE]
        )
        if not ids:
            break
        schema_editor.execute(
            "UPDATE game_game SET finished_at = updated_at WHERE id = ANY(%s) AND finished_at IS NULL",
            [ids],
        )
        total += len(ids)
        print(f"  finished_at: updated {total} rows so far", flush=True)
    print(f"  finished_at: done ({total} rows total)", flush=True)


def backfill_started_at(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    total = 0
    while True:
        ids = list(
            Game.objects.filter(
                status__in=["active", "completed", "abandoned"],
                started_at__isnull=True,
            ).values_list("id", flat=True)[:CHUNK_SIZE]
        )
        if not ids:
            break
        schema_editor.execute(
            """
            UPDATE game_game g
            SET started_at = (
                SELECT MIN(ps.created_at)
                FROM phase_phasestate ps
                JOIN phase_phase pp ON ps.phase_id = pp.id
                WHERE pp.game_id = g.id
            )
            WHERE g.id = ANY(%s)
            AND g.started_at IS NULL
            """,
            [ids],
        )
        total += len(ids)
        print(f"  started_at: updated {total} rows so far", flush=True)
    print(f"  started_at: done ({total} rows total)", flush=True)


def forward(apps, schema_editor):
    print("Backfilling finished_at ...", flush=True)
    backfill_finished_at(apps, schema_editor)
    print("Backfilling started_at ...", flush=True)
    backfill_started_at(apps, schema_editor)


def reverse(apps, schema_editor):
    schema_editor.execute("UPDATE game_game SET finished_at = NULL WHERE finished_at IS NOT NULL")
    schema_editor.execute("UPDATE game_game SET started_at = NULL WHERE started_at IS NOT NULL")
    print("Reversed: cleared started_at and finished_at for all games", flush=True)


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0014_add_game_timestamps"),
        ("phase", "0015_backfill_orders_outcome"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
