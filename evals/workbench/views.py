import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from inspect_ai.log import EvalSample

from select_orders.context import fixture_to_context
from select_orders.exceptions import FixtureError
from select_orders.fixtures import read_fixture, write_fixture
from select_orders.notation import Notation
from select_orders.options import describe_option, option_from_id, option_id
from select_orders.order_sets import label_order_set, order_set_key, order_set_label
from select_orders.types import Context, Fixture
from workbench.exceptions import RunError
from workbench.runs import (
    distinct_order_sets,
    list_runs,
    read_run,
    sample_prompts,
    score,
    summarise,
    unlabelled_order_sets,
    unusable_answers,
)

LABELS = ("reasonable", "unreasonable")
SUMMED = (
    "answers",
    "failed",
    "reasonable",
    "unreasonable",
    "unmarked",
    "order_sets",
    "new",
    "input_tokens",
    "output_tokens",
)


def _error(message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


def _fixture_path(fixture_id: str) -> Path:
    return settings.EVALS_FIXTURES_DIR / f"{fixture_id}.json"


def _fixtures() -> list[Fixture]:
    fixtures = [read_fixture(path) for path in sorted(settings.EVALS_FIXTURES_DIR.glob("*.json"))]
    return [fixture for fixture in fixtures if settings.EVALS_EVAL_SET in fixture["eval_sets"]]


def _summary(fixture: Fixture) -> dict:
    return {"id": fixture["id"], "nation": fixture["nation"], "phase": fixture["phase"]}


def _board(fixture: Fixture, context: Context) -> dict:
    return {**_summary(fixture), "units": context["units"], "supply_centers": fixture.get("supply_centers", [])}


def _describe(order_ids: set[str], context: Context) -> dict[str, dict]:
    names = {province["id"]: province["name"] for province in context["provinces"]}
    described = {}
    for order_id in sorted(order_ids):
        option = option_from_id(order_id)
        described[order_id] = {
            **option,
            "source_name": names.get(option["source"], option["source"]),
            "description": describe_option(option, context),
        }
    return described


def _name(orders: list[str], context: Context) -> str:
    return Notation(context).order_set([option_from_id(order) for order in orders])


def _by_fixture(samples: list[EvalSample]) -> list[tuple[Fixture, list[EvalSample]]]:
    fixtures = {fixture["id"]: fixture for fixture in _fixtures()}
    grouped: dict[str, list[EvalSample]] = {}
    for sample in samples:
        if sample.id in fixtures:
            grouped.setdefault(sample.id, []).append(sample)
    return [(fixtures[fixture_id], grouped[fixture_id]) for fixture_id in sorted(grouped)]


@require_GET
def fixture_list(request):
    return JsonResponse(
        {
            "fixtures": [
                {
                    **_summary(fixture),
                    "labels": dict(Counter(entry["label"] for entry in fixture.get("order_set_labels", []))),
                }
                for fixture in _fixtures()
            ]
        }
    )


@require_GET
def fixture_detail(request, fixture_id):
    path = _fixture_path(fixture_id)
    if not path.exists():
        return _error(f"unknown fixture '{fixture_id}'", 404)
    fixture = read_fixture(path)
    context = fixture_to_context(fixture)

    options = [option_id(option) for option in context["order_options"]]
    labels = fixture.get("order_set_labels", [])
    referenced = {*options, *(order for entry in labels for order in entry["orders"])}

    return JsonResponse(
        {
            **_board(fixture, context),
            "notes": fixture.get("notes", ""),
            "max_orders": fixture.get("max_orders"),
            "options": options,
            "orders": _describe(referenced, context),
            "order_sets": [
                {
                    "orders": entry["orders"],
                    "name": _name(entry["orders"], context),
                    "label": entry["label"],
                    "reason": entry.get("reason", ""),
                }
                for entry in labels
            ],
        }
    )


@require_POST
def order_set_labels(request, fixture_id):
    path = _fixture_path(fixture_id)
    if not path.exists():
        return _error(f"unknown fixture '{fixture_id}'", 404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _error("request body is not JSON", 400)
    orders = body.get("orders") if isinstance(body, dict) else None
    if not isinstance(orders, list) or not all(isinstance(order, str) for order in orders):
        return _error("'orders' must be a list of option ids", 400)
    label = body.get("label")
    if label not in LABELS:
        return _error(f"'label' must be one of {list(LABELS)}", 400)
    reason = body.get("reason")
    if reason is not None and not isinstance(reason, str):
        return _error("'reason' must be a string", 400)

    fixture = read_fixture(path)
    try:
        for order in orders:
            option_from_id(order)
        updated = label_order_set(
            fixture,
            orders,
            label,
            labeller=settings.EVALS_LABELLER,
            labelled_at=datetime.now(UTC).isoformat(timespec="seconds"),
            reason=reason.strip() if reason else None,
        )
        write_fixture(path, updated)
    except FixtureError as e:
        return _error(str(e), 400)
    return JsonResponse({"orders": order_set_key(orders), "labels": updated["order_set_labels"]})


@require_GET
def run_list(request):
    return JsonResponse({"runs": list_runs(settings.EVALS_LOGS_DIR)})


@require_GET
def run_detail(request, name):
    try:
        header, samples = read_run(settings.EVALS_LOGS_DIR, name)
    except RunError as e:
        return _error(str(e), 404)

    fixtures = [{**_summary(fixture), **summarise(fixture, own)} for fixture, own in _by_fixture(samples)]
    totals = {key: sum(fixture[key] for fixture in fixtures) for key in SUMMED}
    return JsonResponse(
        {
            **header,
            **totals,
            "score": score(totals["reasonable"], totals["answers"] - totals["failed"]),
            "fixtures": fixtures,
        }
    )


@require_GET
def run_queue(request, name):
    try:
        _, samples = read_run(settings.EVALS_LOGS_DIR, name)
    except RunError as e:
        return _error(str(e), 404)

    items = []
    matched = 0
    for fixture, own in _by_fixture(samples):
        context = fixture_to_context(fixture)
        order_sets = distinct_order_sets(own)
        unlabelled = unlabelled_order_sets(fixture, order_sets)
        matched += len(order_sets) - len(unlabelled)
        for entry in unlabelled:
            items.append(
                {
                    "fixture": _board(fixture, context),
                    "orders": entry["orders"],
                    "name": _name(entry["orders"], context),
                    "details": _describe(set(entry["orders"]), context),
                    "reasonings": entry["reasonings"],
                }
            )
    return JsonResponse({"matched": matched, "items": items})


@require_GET
def run_fixture(request, name, fixture_id):
    try:
        _, samples = read_run(settings.EVALS_LOGS_DIR, name)
    except RunError as e:
        return _error(str(e), 404)
    found = [(fixture, own) for fixture, own in _by_fixture(samples) if fixture["id"] == fixture_id]
    if not found:
        return _error(f"run '{name}' has no fixture '{fixture_id}'", 404)
    ((fixture, own),) = found

    context = fixture_to_context(fixture)
    order_sets = []
    for entry in distinct_order_sets(own):
        label = order_set_label(fixture, entry["orders"])
        order_sets.append(
            {
                "orders": entry["orders"],
                "name": _name(entry["orders"], context),
                "details": _describe(set(entry["orders"]), context),
                "label": label["label"] if label else None,
                "reason": label.get("reason", "") if label else "",
                "epochs": entry["epochs"],
                "reasonings": entry["reasonings"],
            }
        )
    return JsonResponse(
        {
            "fixture": _board(fixture, context),
            "summary": summarise(fixture, own),
            "order_sets": sorted(order_sets, key=lambda entry: -len(entry["epochs"])),
            "unusable": unusable_answers(own),
        }
    )


@require_GET
def run_prompts(request, name):
    try:
        _, samples = read_run(settings.EVALS_LOGS_DIR, name)
    except RunError as e:
        return _error(str(e), 404)

    first = {}
    for sample in sorted(samples, key=lambda sample: sample.epoch):
        first.setdefault(sample.id, sample)
    return JsonResponse(
        {"prompts": [{"fixture": fixture_id, **sample_prompts(first[fixture_id])} for fixture_id in sorted(first)]}
    )
