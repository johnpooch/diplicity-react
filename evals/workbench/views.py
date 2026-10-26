import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from inspect_ai.log import EvalSample

from games.exceptions import FeedbackError
from games.feedback import feedback_path, phase_key, read_feedback, write_note
from games.play import position
from games.reference import read_reference
from select_orders.context import fixture_to_context
from select_orders.exceptions import FixtureError
from select_orders.fixtures import (
    full_option,
    read_fixture,
    validate_fixture,
    write_fixture,
)
from select_orders.notation import Notation
from select_orders.options import describe_option, option_from_id, option_id
from select_orders.order_sets import label_order_set, order_set_key, order_set_label
from select_orders.types import Context, Fixture
from workbench.exceptions import RunError
from workbench.game_runs import (
    GAME_TASK,
    answer,
    failed_phases,
    game_phases,
    game_result,
    game_summaries,
    has_feedback,
    list_game_runs,
    mean,
    orphaned_feedback,
)
from workbench.runs import (
    distinct_order_sets,
    list_runs,
    read_run,
    run_samples,
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


_parsed_fixtures: dict[Path, tuple[str, Fixture]] = {}


def _cached_fixture(path: Path) -> Fixture:
    text = path.read_text()
    cached = _parsed_fixtures.get(path)
    if cached is None or cached[0] != text:
        cached = _parsed_fixtures[path] = (text, validate_fixture(json.loads(text)))
    return cached[1]


def _fixtures() -> list[Fixture]:
    fixtures = [
        _cached_fixture(path)
        for path in sorted(settings.EVALS_FIXTURES_DIR.glob("*.json"))
    ]
    return [
        fixture
        for fixture in fixtures
        if settings.EVALS_EVAL_SET in fixture["eval_sets"]
    ]


def _summary(fixture: Fixture) -> dict:
    return {"id": fixture["id"], "nation": fixture["nation"], "phase": fixture["phase"]}


def _board(fixture: Fixture, context: Context) -> dict:
    return {
        **_summary(fixture),
        "units": context["units"],
        "supply_centers": fixture.get("supply_centers", []),
    }


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
    return [
        (fixtures[fixture_id], grouped[fixture_id]) for fixture_id in sorted(grouped)
    ]


def _scored(samples: list[EvalSample]) -> tuple[list[dict], dict]:
    summaries = [
        {**_summary(fixture), **summarise(fixture, own)}
        for fixture, own in _by_fixture(samples)
    ]
    totals = {key: sum(summary[key] for summary in summaries) for key in SUMMED}
    return summaries, {
        **totals,
        "score": score(totals["reasonable"], totals["answers"] - totals["failed"]),
    }


@require_GET
def fixture_list(request):
    return JsonResponse(
        {
            "fixtures": [
                {
                    **_summary(fixture),
                    "labels": dict(
                        Counter(
                            entry["label"]
                            for entry in fixture.get("order_set_labels", [])
                        )
                    ),
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
    if not isinstance(orders, list) or not all(
        isinstance(order, str) for order in orders
    ):
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
    return JsonResponse(
        {"orders": order_set_key(orders), "labels": updated["order_set_labels"]}
    )


@require_GET
def run_list(request):
    runs = []
    for header in list_runs(settings.EVALS_LOGS_DIR):
        summaries, totals = _scored(
            run_samples(settings.EVALS_LOGS_DIR, header["name"])
        )
        runs.append(
            {
                **header,
                **totals,
                "fixture_ids": [summary["id"] for summary in summaries],
            }
        )
    return JsonResponse({"runs": runs})


@require_GET
def run_detail(request, name):
    try:
        header, samples = read_run(settings.EVALS_LOGS_DIR, name)
    except RunError as e:
        return _error(str(e), 404)

    fixtures, totals = _scored(samples)
    return JsonResponse({**header, **totals, "fixtures": fixtures})


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
    found = [
        (fixture, own)
        for fixture, own in _by_fixture(samples)
        if fixture["id"] == fixture_id
    ]
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
        {
            "prompts": [
                {"fixture": fixture_id, **sample_prompts(first[fixture_id])}
                for fixture_id in sorted(first)
            ]
        }
    )


def _reference(nation: str) -> dict | None:
    reference = read_reference(settings.EVALS_REFERENCE_DIR, nation)
    return None if reference is None else {"games": reference["games"]}


def _means(results: list[dict]) -> dict:
    return {
        "centres": mean([result["centres"] for result in results]),
        "share": mean([result["share"] for result in results]),
    }


def _game_run(name: str) -> tuple[dict, list[EvalSample]]:
    header, samples = read_run(settings.EVALS_LOGS_DIR, name, GAME_TASK)
    return {
        **header,
        "nation": samples[0].metadata["nation"] if samples else None,
    }, samples


def _game(name: str, seed: int) -> tuple[dict, EvalSample]:
    header, samples = _game_run(name)
    found = [sample for sample in samples if sample.id == seed]
    if not found:
        raise RunError(f"game run '{name}' has no game with seed {seed}")
    return header, found[0]


def _feedback(feedback: dict | None) -> dict:
    feedback = feedback or {}
    return {
        "overall": feedback.get("overall", ""),
        "phases": feedback.get("phases", {}),
    }


def _game_phase(phase: dict, following: dict | None, nation: str) -> dict:
    context = fixture_to_context(
        position(phase["phase"], phase["units"], phase["supply_centers"], nation, [])
    )
    results = {
        (entry["nation"], entry["source"]): entry["result"]
        for entry in phase["resolutions"]
    }
    submitted = [
        (player, option_id(full_option(option)), option["source"])
        for player, options in sorted(phase["orders"].items())
        for option in options
    ]
    details = _describe({order for _, order, _ in submitted}, context)
    orders = [
        {
            "nation": player,
            "id": order,
            **details[order],
            "result": results.get((player, source)),
        }
        for player, order, source in submitted
    ]
    notation = Notation(context)
    given = answer(phase, nation)
    return {
        "key": phase_key(phase["phase"]),
        "phase": phase["phase"],
        "units": context["units"],
        "supply_centers": phase["supply_centers"],
        "dislodged": (
            [unit["province"] for unit in following["units"] if unit.get("dislodged")]
            if following
            else []
        ),
        "orders": orders,
        "answer": (
            None
            if given is None
            else {
                **given,
                "orders": [
                    {**entry, "name": notation.order(option_from_id(entry["id"]))}
                    for entry in orders
                    if entry["nation"] == nation
                ],
            }
        ),
    }


@require_GET
def game_run_list(request):
    runs, seeds = [], {}
    for header in list_game_runs(settings.EVALS_LOGS_DIR):
        summaries = game_summaries(settings.EVALS_LOGS_DIR, header["name"])
        results = [game_result(summary.metadata) for summary in summaries]
        seeds[header["name"]] = {result["seed"] for result in results}
        runs.append(
            {
                **header,
                **_means(results),
                "nation": summaries[0].metadata["nation"] if summaries else None,
                "games": len(results),
                "with_feedback": sum(
                    has_feedback(
                        settings.EVALS_FEEDBACK_DIR, header["name"], result["seed"]
                    )
                    for result in results
                ),
            }
        )
    nations = sorted({run["nation"] for run in runs if run["nation"]})
    return JsonResponse(
        {
            "runs": runs,
            "references": {nation: _reference(nation) for nation in nations},
            "orphans": orphaned_feedback(settings.EVALS_FEEDBACK_DIR, seeds),
        }
    )


@require_GET
def game_run_detail(request, name):
    try:
        header, samples = _game_run(name)
    except RunError as e:
        return _error(str(e), 404)

    games = [
        {
            **game_result(sample.metadata),
            "failed": failed_phases(sample),
            "feedback": has_feedback(settings.EVALS_FEEDBACK_DIR, name, sample.id),
        }
        for sample in sorted(samples, key=lambda sample: sample.id)
    ]
    return JsonResponse(
        {
            **header,
            **_means(games),
            "games": games,
            "reference": _reference(header["nation"]) if header["nation"] else None,
            "opening": sample_prompts(samples[0]) if samples else None,
        }
    )


@require_GET
def game_detail(request, name, seed):
    try:
        header, sample = _game(name, seed)
    except RunError as e:
        return _error(str(e), 404)
    try:
        feedback = read_feedback(feedback_path(settings.EVALS_FEEDBACK_DIR, name, seed))
    except FeedbackError as e:
        return _error(str(e), 409)

    nation = sample.metadata["nation"]
    phases = game_phases(sample)
    return JsonResponse(
        {
            **header,
            **game_result(sample.metadata),
            "final_centres": sample.metadata["centres"],
            "phases": [
                _game_phase(
                    phase,
                    phases[index + 1] if index + 1 < len(phases) else None,
                    nation,
                )
                for index, phase in enumerate(phases)
            ],
            "feedback": _feedback(feedback),
        }
    )


@require_http_methods(["PUT"])
def game_feedback(request, name, seed):
    try:
        _, sample = _game(name, seed)
    except RunError as e:
        return _error(str(e), 404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _error("request body is not JSON", 400)
    if not isinstance(body, dict):
        return _error("request body must be an object", 400)
    phase, note = body.get("phase"), body.get("note")
    if phase is not None and not isinstance(phase, str):
        return _error("'phase' must be a phase key or null for the overall note", 400)
    if not isinstance(note, str):
        return _error("'note' must be a string", 400)

    keys = {phase_key(entry["phase"]) for entry in game_phases(sample)}
    try:
        updated = write_note(
            feedback_path(settings.EVALS_FEEDBACK_DIR, name, seed),
            sample.metadata["nation"],
            keys,
            phase,
            note,
        )
    except FeedbackError as e:
        return _error(str(e), 400)
    return JsonResponse(_feedback(updated))
