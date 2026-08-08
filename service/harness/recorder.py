import hashlib
import json
import re
from pathlib import Path

from django.db.migrations.loader import MigrationLoader
from django.utils.dateparse import parse_datetime

from harness.constants import EvalRunKind
from harness.exceptions import RecordingError

MIGRATIONS_DIR = Path(__file__).with_name("migrations")

STDERR_METRIC = "stderr"

TEMPLATE = """import datetime

from django.db import migrations

RUN = {{
{run}}}

SCORES = [
{scores}]


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
        ("harness", "{dependency}"),
    ]

    operations = [
        migrations.RunPython(record, unrecord),
    ]
"""


def extract(log, *, model=None):
    if log.status != "success":
        raise RecordingError(f"eval did not succeed: status {log.status}")
    if log.results is None:
        raise RecordingError("eval produced no results")
    revision = log.eval.revision
    if revision is None:
        raise RecordingError("eval was not run from a git checkout, so its commit is unknown")
    if revision.dirty:
        raise RecordingError("working tree is dirty, so the recorded commit would not describe the run")
    run = {
        "kind": EvalRunKind.EVAL,
        "model": model or log.eval.model,
        "commit": revision.commit,
        "dataset": _dataset_digest(log.eval),
        "epochs": log.eval.config.epochs or 1,
        "eval_id": log.eval.eval_id,
        "ran_at": parse_datetime(log.eval.created),
    }
    return {"run": run, "scores": _score_rows(log)}


def write_migration(payload, *, directory=MIGRATIONS_DIR):
    number, dependency = _next_migration(directory)
    name = f"{number:04d}_record_{_model_slug(payload['run']['model'])}_{payload['run']['commit']}.py"
    run = "".join(f"    {_literal(key)}: {_literal(value)},\n" for key, value in payload["run"].items())
    scores = "".join(f"    {_mapping(score)},\n" for score in payload["scores"])
    path = directory / name
    path.write_text(TEMPLATE.format(run=run, scores=scores, dependency=dependency))
    return path


def record(log, *, model=None, directory=MIGRATIONS_DIR):
    return write_migration(extract(log, model=model), directory=directory)


def _dataset_digest(spec):
    if not spec.dataset.location:
        return ""
    path = Path(spec.dataset.location)
    if not path.is_absolute() and spec.task_file:
        path = Path(spec.task_file).parent / path
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError as error:
        raise RecordingError(f"dataset {path} could not be read: {error}")


def _score_rows(log):
    rows = []
    for score in log.results.scores:
        if not score.scored_samples:
            continue
        stderr = score.metrics.get(STDERR_METRIC)
        for name, metric in score.metrics.items():
            if name == STDERR_METRIC:
                continue
            rows.append(
                {
                    "scorer": score.name,
                    "metric": name,
                    "value": metric.value,
                    "stderr": None if stderr is None else stderr.value,
                    "sample_count": score.scored_samples,
                }
            )
    return rows


def _next_migration(directory):
    leaves = MigrationLoader(None, ignore_no_migrations=True).graph.leaf_nodes("harness")
    if not leaves:
        raise RecordingError("harness has no migrations, so there is nothing to record against")
    dependency = leaves[0][1]
    existing = [int(path.name[:4]) for path in directory.glob("[0-9][0-9][0-9][0-9]_*.py")]
    return max(existing, default=0) + 1, dependency


def _literal(value):
    if isinstance(value, str):
        return json.dumps(value)
    return repr(value)


def _mapping(mapping):
    body = ", ".join(f"{_literal(key)}: {_literal(value)}" for key, value in mapping.items())
    return f"{{{body}}}"


def _model_slug(model):
    return re.sub(r"[^a-z0-9]+", "_", model.rsplit("/", 1)[-1].lower()).strip("_")
