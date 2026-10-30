"""Small immutable contracts shared by loading, detection, and reporting."""

from dataclasses import dataclass
from pathlib import Path


class DatasetError(ValueError):
    """An input cannot be audited completely and must not produce a clean result."""


@dataclass(frozen=True)
class Sample:
    path: Path
    split: str


@dataclass(frozen=True)
class Dataset:
    yaml_path: Path
    root: Path
    samples: tuple[Sample, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    kind: str
    evidence: str
    group_id: str
    members: tuple[Sample, ...]
    similarity: dict | None = None


@dataclass(frozen=True)
class ProvenanceRecord:
    path: Path
    video_id: str | None
    session_id: str | None
    evidence: str
    source_ref: str | None


@dataclass(frozen=True)
class Provenance:
    records: dict[Path, ProvenanceRecord]
    warnings: tuple[str, ...]
    manifest_path: Path | None
