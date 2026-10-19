def share(centres: dict[str, int], nation: str, solo: int) -> float:
    soloist = next((other for other, count in centres.items() if count >= solo), None)
    if soloist is not None:
        return 100.0 if soloist == nation else 0.0
    total = sum(count**2 for count in centres.values())
    return 100 * centres[nation] ** 2 / total if total else 0.0
