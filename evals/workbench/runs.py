from functools import lru_cache
from pathlib import Path

from inspect_ai.log import EvalLog, EvalSample, read_eval_log

from select_orders.exceptions import ParsingError
from select_orders.options import option_id
from select_orders.order_sets import order_set_key, order_set_label
from select_orders.parser import parse_completion
from select_orders.types import Fixture
from select_orders.utils import parse_json_object
from workbench.exceptions import RunError

MODEL_TASK = "select_orders"
SUCCESS = "success"
REASONABLE = "reasonable"


@lru_cache(maxsize=64)
def _read(path: str, modified: float, header_only: bool) -> EvalLog:
    return read_eval_log(path, header_only=header_only)


def _paths(logs_dir: Path) -> list[Path]:
    return sorted(logs_dir.glob("*.eval"), reverse=True)


def _header(path: Path, log: EvalLog) -> dict:
    return {
        "name": path.stem,
        "id": log.eval.eval_id,
        "task": log.eval.task,
        "model": log.eval.model,
        "created": log.eval.created,
        "status": log.status,
    }


def list_runs(logs_dir: Path) -> list[dict]:
    headers = [_header(path, _read(str(path), path.stat().st_mtime, True)) for path in _paths(logs_dir)]
    return [header for header in headers if header["task"] == MODEL_TASK and header["status"] == SUCCESS]


def read_run(logs_dir: Path, name: str) -> tuple[dict, list[EvalSample]]:
    if name not in {header["name"] for header in list_runs(logs_dir)}:
        raise RunError(f"unknown run '{name}'")
    path = logs_dir / f"{name}.eval"
    log = _read(str(path), path.stat().st_mtime, False)
    return _header(path, log), log.samples or []


def sample_problem(sample: EvalSample) -> str | None:
    if sample.error is not None:
        return sample.error.message
    try:
        parse_completion(sample.output.completion, sample.metadata["context"])
    except ParsingError as e:
        return str(e)
    return None


def sample_orders(sample: EvalSample) -> list[str] | None:
    if sample_problem(sample) is not None:
        return None
    orders = parse_completion(sample.output.completion, sample.metadata["context"])
    return order_set_key([option_id(order) for order in orders])


def sample_reasoning(sample: EvalSample) -> str | None:
    try:
        reasoning = parse_json_object(sample.output.completion).get("reasoning")
    except ParsingError:
        return None
    return reasoning if isinstance(reasoning, str) else None


def sample_prompts(sample: EvalSample) -> dict[str, str]:
    return {message.role: message.text for message in sample.input if message.role in ("system", "user")}


def distinct_order_sets(samples: list[EvalSample]) -> list[dict]:
    produced: dict[tuple[str, ...], dict] = {}
    for sample in sorted(samples, key=lambda sample: sample.epoch):
        orders = sample_orders(sample)
        if orders is None:
            continue
        entry = produced.setdefault(tuple(orders), {"orders": orders, "epochs": [], "reasonings": []})
        entry["epochs"].append(sample.epoch)
        reasoning = sample_reasoning(sample)
        if reasoning:
            entry["reasonings"].append({"epoch": sample.epoch, "reasoning": reasoning})
    return list(produced.values())


def unusable_answers(samples: list[EvalSample]) -> list[dict]:
    return [
        {"epoch": sample.epoch, "problem": problem, "completion": sample.output.completion}
        for sample in sorted(samples, key=lambda sample: sample.epoch)
        if (problem := sample_problem(sample)) is not None
    ]


def unlabelled_order_sets(fixture: Fixture, order_sets: list[dict]) -> list[dict]:
    return [entry for entry in order_sets if order_set_label(fixture, entry["orders"]) is None]


def score(reasonable: int, order_sets: int) -> float | None:
    return reasonable / order_sets if order_sets else None


def summarise(fixture: Fixture, samples: list[EvalSample]) -> dict:
    order_sets = distinct_order_sets(samples)
    labels = [order_set_label(fixture, entry["orders"]) for entry in order_sets]
    reasonable = sum(1 for label in labels if label is not None and label["label"] == REASONABLE)
    new = len(unlabelled_order_sets(fixture, order_sets))
    return {
        "answers": len(samples),
        "order_sets": len(order_sets),
        "reasonable": reasonable,
        "unreasonable": len(order_sets) - new - reasonable,
        "new": new,
        "matched": len(order_sets) - new,
        "unanswered": sum(1 for sample in samples if sample_orders(sample) is None),
        "score": score(reasonable, len(order_sets)),
    }
