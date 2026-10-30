"""Streaming SHA-256 groups: linear work in input bytes, no pairwise image matrix."""

import hashlib
from collections import defaultdict
from pathlib import Path

from videosplitguard.models import Finding, Sample


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    before = path.stat()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise OSError(f"Image changed while hashing: {path}")
    return digest.hexdigest()


def hash_all(samples: tuple[Sample, ...]) -> dict[Path, str]:
    cache = {}
    for sample in samples:
        if sample.path not in cache:
            cache[sample.path] = sha256_file(sample.path)
    return cache


def detect_exact(
    samples: tuple[Sample, ...], hashes: dict[Path, str] | None = None
) -> tuple[Finding, ...]:
    cache = hashes if hashes is not None else hash_all(samples)
    groups = defaultdict(list)
    for sample in samples:
        groups[cache[sample.path]].append(sample)
    return tuple(
        Finding(
            "exact_overlap",
            "confirmed_shared_path" if len({m.path for m in members}) == 1 else "confirmed_bytes",
            digest,
            tuple(members),
        )
        for digest, members in sorted(groups.items())
        if len({sample.split for sample in members}) > 1
    )
