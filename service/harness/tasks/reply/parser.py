from harness.utils import parse_json_object


def parse_completion(completion: str) -> str | None:
    data = parse_json_object(completion)
    message = (data.get("message") or "").strip()
    return message or None
