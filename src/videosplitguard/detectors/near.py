"""Opt-in CPU dHash candidates with hard bounds on images and output groups."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from videosplitguard.models import DatasetError, Finding, Sample
from videosplitguard.similarity import grayscale, require_numpy, score_pair

MAX_IMAGES = 2000
MAX_FINDINGS = 500
MAX_PIXELS_PER_IMAGE = 16_000_000


@dataclass(frozen=True)
class NearResult:
    status: str
    findings: tuple[Finding, ...]
    images_considered: int
    comparisons: int
    truncated: bool
    reason: str | None


def _dhash(path: Path) -> int:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise DatasetError(
            "Near-duplicate checking requires Pillow; install videosplitguard[similarity]"
        ) from exc
    try:
        with Image.open(path) as source:
            if source.width * source.height > MAX_PIXELS_PER_IMAGE:
                raise DatasetError(
                    f"Near-duplicate image exceeds {MAX_PIXELS_PER_IMAGE} pixels: {path}"
                )
            source.draft("L", (512, 512))
            image = (
                ImageOps.exif_transpose(source)
                .convert("L")
                .resize((9, 8), Image.Resampling.LANCZOS)
            )
            pixels = image.tobytes()
    except Image.DecompressionBombError as exc:
        raise DatasetError(f"Image exceeds Pillow's safe decoding limit: {path}") from exc
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | int(pixels[row * 9 + col] > pixels[row * 9 + col + 1])
    return bits


def detect_near(
    samples: tuple[Sample, ...], exact: tuple[Finding, ...], threshold: int = 6
) -> NearResult:
    if not 0 <= threshold <= 64:
        raise DatasetError("Near-duplicate threshold must be from 0 to 64")
    paths = sorted({sample.path for sample in samples})
    if len(paths) > MAX_IMAGES:
        return NearResult(
            "NOT VERIFIED",
            (),
            0,
            0,
            False,
            f"Skipped {len(paths)} images: optional similarity limit is {MAX_IMAGES} images.",
        )
    by_path: dict[Path, tuple[Sample, ...]] = {
        path: tuple(sample for sample in samples if sample.path == path) for path in paths
    }
    require_numpy()
    normalized = {}
    hashes = {path: _dhash(path) for path in paths}
    exact_group = {member.path: finding.group_id for finding in exact for member in finding.members}
    results = []
    comparisons = 0
    for i, left in enumerate(paths):
        for right in paths[i + 1 :]:
            if not any(a.split != b.split for a in by_path[left] for b in by_path[right]):
                continue
            if exact_group.get(left) and exact_group.get(left) == exact_group.get(right):
                continue
            comparisons += 1
            distance = (hashes[left] ^ hashes[right]).bit_count()
            if distance > threshold:
                continue
            if len(results) == MAX_FINDINGS:
                return NearResult(
                    "NOT VERIFIED",
                    tuple(results),
                    len(paths),
                    comparisons,
                    True,
                    f"Stopped after {MAX_FINDINGS} candidates; further pairs were not checked.",
                )
            pair_id = hashlib.sha256(
                (left.as_posix() + "\0" + right.as_posix()).encode("utf-8")
            ).hexdigest()[:16]
            for path in (left, right):
                if path not in normalized:
                    normalized[path] = grayscale(path)
            results.append(
                Finding(
                    "near_duplicate_candidate",
                    "perceptual_dhash",
                    f"dhash-{pair_id}-distance-{distance}",
                    by_path[left] + by_path[right],
                    score_pair(normalized[left], normalized[right], distance),
                )
            )
    return NearResult(
        "NOT VERIFIED" if results else "PASS",
        tuple(results),
        len(paths),
        comparisons,
        False,
        None,
    )
