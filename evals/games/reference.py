import asyncio
import json
from pathlib import Path

from games.play import dumbbot_seats, play, solo_centres
from games.scoring import share


def reference_path(directory: Path, nation: str) -> Path:
    return directory / f"{nation.lower()}.json"


def reference_game(seed: int, nation: str) -> dict:
    game = asyncio.run(play(dumbbot_seats(seed), nation))
    return {
        "seed": seed,
        "centres": game["centres"][nation],
        "share": share(game["centres"], nation, solo_centres()),
    }


def write_reference(directory: Path, nation: str, games: list[dict]) -> Path:
    path = reference_path(directory, nation)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"nation": nation, "games": games}, indent=2) + "\n")
    return path


def read_reference(directory: Path, nation: str) -> dict | None:
    path = reference_path(directory, nation)
    return json.loads(path.read_text()) if path.exists() else None
