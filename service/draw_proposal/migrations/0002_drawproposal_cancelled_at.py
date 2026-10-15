from django.db import migrations, models
from django.db.models import F


def backfill_cancelled_at(apps, schema_editor):
    DrawProposal = apps.get_model("draw_proposal", "DrawProposal")
    DrawProposal.objects.filter(cancelled=True).update(cancelled_at=F("updated_at"))


class Migration(migrations.Migration):

    dependencies = [
        ("draw_proposal", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="drawproposal",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_cancelled_at, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE draw_proposal_drawproposal ALTER COLUMN cancelled SET DEFAULT false",
                    reverse_sql="ALTER TABLE draw_proposal_drawproposal ALTER COLUMN cancelled DROP DEFAULT",
                ),
            ],
            state_operations=[
                migrations.RemoveField(model_name="drawproposal", name="cancelled"),
            ],
        ),
    ]
