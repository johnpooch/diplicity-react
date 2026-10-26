import hashlib
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from inspect_ai.dataset import Dataset
from inspect_ai.log import read_eval_log

from select_orders.exceptions import PromptError

ADJECTIVES = tuple("""
    amber ancient autumn bitter bold brave brisk bronze calm candid clever cobalt copper
    crimson crisp dapper daring dusky eager early earnest fabled fierce fleet frosty gentle
    gilded golden grand hardy hidden hollow humble icy idle ivory jolly keen lively lofty
    lucky mellow merry misty modest nimble noble olive pale patient plucky proud quiet rapid
    restless rustic scarlet silent silver steady stout sunny swift wary
    """.split())

NOUNS = tuple("""
    anchor archer badger banner barge beacon bishop bastion canal castle citadel cliff comet
    compass convoy crown delta dune eagle envoy falcon fjord fortress frigate garrison
    glacier harbour herald heron island lantern marsh meadow orchard otter outpost palace
    pennant pilgrim plateau rampart raven reef regent ridge river sentinel shoal squire
    steppe strait summit tempest thistle tower treaty tundra valley vanguard viceroy
    vineyard walrus warden wolf
    """.split())


def _digest(parts: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def prompt_digest(dataset: Dataset) -> str:
    return _digest(
        part
        for sample in sorted(dataset, key=lambda sample: str(sample.id))
        for part in (str(sample.id), *(message.text for message in sample.input))
    )


def game_prompt_digest(nation: str, system: str, user: str) -> str:
    return _digest((nation, system, user))


def _name_for(digest: str, day: date, taken: set[str]) -> str:
    start = int(digest, 16)
    for step in range(len(ADJECTIVES) * len(NOUNS)):
        index = (start + step) % (len(ADJECTIVES) * len(NOUNS))
        adjective, noun = ADJECTIVES[index // len(NOUNS)], NOUNS[index % len(NOUNS)]
        name = f"{adjective}-{noun}-{day.strftime('%b').lower()}-{day.day}"
        if name not in taken:
            return name
    raise PromptError(f"every prompt name for {day} is taken")


def _logged_prompts(logs_dir: Path) -> dict[str, str]:
    prompts = {}
    for path in sorted(logs_dir.glob("*.eval")):
        prompt = (read_eval_log(str(path), header_only=True).eval.metadata or {}).get(
            "prompt"
        )
        if prompt:
            prompts.setdefault(prompt["digest"], prompt["name"])
    return prompts


def prompt_name(digest: str, logs_dir: Path, day: date) -> str:
    logged = _logged_prompts(logs_dir)
    return logged.get(digest) or _name_for(digest, day, set(logged.values()))
