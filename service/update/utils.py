def parse_version(value):
    parts = [int(part) if part.isdecimal() else 0 for part in value.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)
