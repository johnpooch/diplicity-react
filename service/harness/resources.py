from importlib import resources


def load_prompt(package: str, name: str) -> str:
    return resources.files(package).joinpath(name).read_text(encoding="utf-8").strip()
