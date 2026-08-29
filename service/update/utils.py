def parse_version(value):
    return tuple(int(part) if part.isdigit() else 0 for part in value.split("."))
