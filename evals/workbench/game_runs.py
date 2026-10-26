from functools import lru_cache
from pathlib import Path

from inspect_ai.log import EvalSample, EvalSampleSummary, read_eval_log_sample_summaries

from games.evals import GAME_STORE_KEY
from games.exceptions import FeedbackError
from games.feedback import feedback_path, read_feedback
from games.play import solo_centres
from games.scoring import share
from workbench.runs import list_runs

GAME_TASK = "play_game"


@lru_cache(maxsize=64)
def _summaries(path: str, modified: float) -> list[EvalSampleSummary]:
    return read_eval_log_sample_summaries(path)


def list_game_runs(logs_dir: Path) -> list[dict]:
    return list_runs(logs_dir, GAME_TASK)


def game_summaries(logs_dir: Path, name: str) -> list[EvalSampleSummary]:
    path = logs_dir / f"{name}.eval"
    return _summaries(str(path), path.stat().st_mtime)


def game_result(metadata: dict) -> dict:
    nation = metadata["nation"]
    return {
        "seed": metadata["seed"],
        "centres": metadata["centres"][nation],
        "share": share(metadata["centres"], nation, solo_centres()),
        "paired_centres": metadata["paired_centres"][nation],
        "paired_share": share(metadata["paired_centres"], nation, solo_centres()),
        "end": metadata["end"],
    }


def game_phases(sample: EvalSample) -> list[dict]:
    return sample.store[GAME_STORE_KEY]


def answer(phase: dict, nation: str) -> dict | None:
    return phase.get("answers", {}).get(nation)


def failed_phases(sample: EvalSample) -> int:
    nation = sample.metadata["nation"]
    return sum(
        1
        for phase in game_phases(sample)
        if (given := answer(phase, nation)) is not None and given["problem"]
    )


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def orphaned_feedback(feedback_dir: Path, seeds: dict[str, set[int]]) -> list[dict]:
    orphans = []
    for path in sorted(feedback_dir.glob("*/*.json")):
        run, seed = path.parent.name, path.stem
        problem = None
        if run not in seeds:
            problem = f"no game run '{run}' in the logs"
        elif not seed.isdigit() or int(seed) not in seeds[run]:
            problem = f"game run '{run}' has no game with seed {seed}"
        else:
            try:
                read_feedback(path)
            except FeedbackError as e:
                problem = str(e)
        if problem is not None:
            orphans.append(
                {"path": str(path.relative_to(feedback_dir.parent)), "problem": problem}
            )
    return orphans


def has_feedback(feedback_dir: Path, run: str, seed: int) -> bool:
    return feedback_path(feedback_dir, run, seed).exists()
