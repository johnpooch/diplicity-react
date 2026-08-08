import datetime

from django.db import migrations

RUN = {
    "kind": "eval",
    "model": "dumbbot",
    "commit": "96a3136",
    "dataset": "beb637fa7319",
    "epochs": 20,
    "eval_id": "dE93AkAW5DXNLgKWdKFdCo",
    "ran_at": datetime.datetime(2026, 8, 8, 12, 19, 32, tzinfo=datetime.timezone.utc),
}

SCORES = [
    {"scorer": "legality", "metric": "accuracy", "value": 1.0, "stderr": 0.0, "sample_count": 10},
    {"scorer": "deduplication", "metric": "accuracy", "value": 1.0, "stderr": 0.0, "sample_count": 10},
    {"scorer": "coverage", "metric": "accuracy", "value": 1.0, "stderr": 0.0, "sample_count": 10},
    {"scorer": "support_coherence", "metric": "accuracy", "value": 1.0, "stderr": 0.0, "sample_count": 10},
    {"scorer": "convoy_coherence", "metric": "accuracy", "value": 1.0, "stderr": 0.0, "sample_count": 10},
    {"scorer": "quality_strong", "metric": "accuracy", "value": 0.75, "stderr": 0.25, "sample_count": 4},
    {"scorer": "quality_avoidance", "metric": "accuracy", "value": 1.0, "stderr": 0.0, "sample_count": 4},
]


def record(apps, schema_editor):
    EvalRun = apps.get_model("harness", "EvalRun")
    EvalScore = apps.get_model("harness", "EvalScore")
    run = EvalRun.objects.create(**RUN)
    for score in SCORES:
        EvalScore.objects.create(run=run, **score)


def unrecord(apps, schema_editor):
    EvalRun = apps.get_model("harness", "EvalRun")
    EvalRun.objects.filter(eval_id=RUN["eval_id"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("harness", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(record, unrecord),
    ]
