import json
from pathlib import Path

from jsonschema import Draft202012Validator

from games.exceptions import FeedbackError

SEASONS = ("Spring", "Fall")
PHASE_TYPES = ("Movement", "Retreat", "Adjustment")
PHASE_KEY_PATTERN = rf"^\d{{4}}-({'|'.join(SEASONS)})-({'|'.join(PHASE_TYPES)})$"

FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "nation": {"type": "string"},
        "overall": {"type": "string", "pattern": r"\S"},
        "phases": {
            "type": "object",
            "propertyNames": {"pattern": PHASE_KEY_PATTERN},
            "additionalProperties": {"type": "string", "pattern": r"\S"},
        },
    },
    "required": ["nation"],
    "additionalProperties": False,
}

_VALIDATOR = Draft202012Validator(FEEDBACK_SCHEMA)


def phase_key(phase: dict) -> str:
    return f"{phase['year']}-{phase['season']}-{phase['type']}"


def _chronological(key: str) -> tuple[int, int, int]:
    year, season, phase_type = key.split("-")
    return int(year), SEASONS.index(season), PHASE_TYPES.index(phase_type)


def feedback_path(directory: Path, run: str, seed: int) -> Path:
    return directory / run / f"{seed}.json"


def validate_feedback(feedback: dict, path: Path) -> dict:
    error = next(
        iter(
            sorted(
                _VALIDATOR.iter_errors(feedback), key=lambda e: list(e.absolute_path)
            )
        ),
        None,
    )
    if error is not None:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise FeedbackError(
            f"feedback '{path}' violates schema at {location}: {error.message}"
        )
    return feedback


def read_feedback(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        feedback = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise FeedbackError(f"feedback '{path}' is not JSON: {e}") from e
    return validate_feedback(feedback, path)


def write_note(
    path: Path, nation: str, phase_keys: set[str], key: str | None, note: str
) -> dict:
    if key is not None and key not in phase_keys:
        raise FeedbackError(f"the game has no phase '{key}'")
    feedback = read_feedback(path) or {"nation": nation}
    if feedback["nation"] != nation:
        raise FeedbackError(
            f"feedback '{path}' is for {feedback['nation']}, not {nation}"
        )
    overall = feedback.get("overall")
    phases = dict(feedback.get("phases", {}))
    if key is None:
        overall = note
    else:
        phases[key] = note
    updated = {"nation": nation}
    if overall and overall.strip():
        updated["overall"] = overall
    kept = {
        phase: phases[phase]
        for phase in sorted(phases, key=_chronological)
        if phases[phase].strip()
    }
    if kept:
        updated["phases"] = kept
    if len(updated) == 1:
        path.unlink(missing_ok=True)
        if path.parent.exists() and not any(path.parent.iterdir()):
            path.parent.rmdir()
        return updated
    validate_feedback(updated, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(updated, indent=2) + "\n")
    return updated
