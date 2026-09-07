import hashlib
import zipfile
from pathlib import Path

CHECKSUM_CHUNK_SIZE = 1024 * 1024


def parse_version(value):
    parts = [int(part) if part.isdecimal() else 0 for part in value.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def is_numeric_version(value):
    parts = value.split(".")
    return bool(value) and all(part.isdecimal() for part in parts)


def write_bundle_zip(dist, destination):
    dist = Path(dist)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(path for path in dist.rglob("*") if path.is_file()):
            archive.write(path, path.relative_to(dist))
    return destination


def sha256_checksum(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHECKSUM_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
