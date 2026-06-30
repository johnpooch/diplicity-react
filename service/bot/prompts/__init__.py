from importlib import resources


def load_prompt(name: str) -> str:
    return resources.files("bot.prompts").joinpath(name).read_text(encoding="utf-8").strip()
