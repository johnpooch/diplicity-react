from django.db import migrations


def complete_phases_of_finished_games(apps, schema_editor):
    schema_editor.execute("""
        UPDATE phase_phase
        SET status = 'completed',
            scheduled_resolution = NULL,
            resolution_job_id = NULL
        FROM game_game
        WHERE phase_phase.game_id = game_game.id
          AND game_game.status IN ('completed', 'abandoned')
          AND phase_phase.status <> 'completed'
    """)


class Migration(migrations.Migration):

    dependencies = [
        ("phase", "0017_phase_processing_started_at_alter_phase_status"),
        ("game", "0023_backfill_commitment_requirement"),
    ]

    operations = [
        migrations.RunPython(
            complete_phases_of_finished_games,
            migrations.RunPython.noop,
        ),
    ]
