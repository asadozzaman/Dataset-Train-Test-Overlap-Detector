"""Strict, explicit source provenance; no origin is inferred from file names."""

import csv
from pathlib import Path

from videosplitguard.models import Dataset, DatasetError, Provenance, ProvenanceRecord

REQUIRED_COLUMNS = {"path", "video_id", "session_id", "evidence", "source_ref"}


def load_provenance(dataset: Dataset, manifest_path: Path | None) -> Provenance:
    if manifest_path is None:
        return Provenance({}, (), None)
    manifest_path = manifest_path.resolve()
    try:
        stream = manifest_path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise DatasetError(f"Cannot read provenance CSV: {exc}") from exc
    records: dict[Path, ProvenanceRecord] = {}
    try:
        with stream:
            reader = csv.DictReader(stream, strict=True)
            if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
                raise DatasetError(
                    "Provenance CSV requires: path,video_id,session_id,evidence,source_ref"
                )
            if len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise DatasetError("Provenance CSV has duplicate column names")
            video_sessions: dict[str, str] = {}
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    raise DatasetError(f"Extra CSV fields on line {line_number}")
                if any(value is None for value in row.values()):
                    raise DatasetError(f"Missing CSV fields on line {line_number}")
                raw_path = (row["path"] or "").strip()
                if not raw_path:
                    raise DatasetError(f"Empty provenance path on line {line_number}")
                spelling = Path(raw_path.replace("\\", "/"))
                if spelling.is_absolute() or ":" in raw_path:
                    raise DatasetError(
                        f"Provenance path must be dataset-relative on line {line_number}"
                    )
                path = (dataset.root / spelling).resolve()
                if not path.is_relative_to(dataset.root):
                    raise DatasetError(
                        f"Provenance path escapes dataset root on line {line_number}"
                    )
                if path in records:
                    raise DatasetError(
                        f"Duplicate provenance path on line {line_number}: {raw_path}"
                    )
                video_id = (row["video_id"] or "").strip() or None
                session_id = (row["session_id"] or "").strip() or None
                evidence = (row["evidence"] or "").strip().lower()
                source_ref = (row["source_ref"] or "").strip() or None
                if evidence not in {"verified", "unverified"}:
                    raise DatasetError(
                        f"Evidence must be verified or unverified on line {line_number}"
                    )
                if evidence == "verified" and not source_ref:
                    raise DatasetError(f"Verified row requires source_ref on line {line_number}")
                if video_id and session_id:
                    previous = video_sessions.setdefault(video_id, session_id)
                    if previous != session_id:
                        raise DatasetError(
                            f"Video {video_id!r} has conflicting session IDs on line {line_number}"
                        )
                records[path] = ProvenanceRecord(path, video_id, session_id, evidence, source_ref)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DatasetError(f"Invalid provenance CSV: {exc}") from exc
    image_paths = {sample.path for sample in dataset.samples}
    unused = sorted(set(records) - image_paths)
    warnings = ()
    if unused:
        warnings = (f"Provenance CSV has {len(unused)} row(s) not present in the dataset.",)
    return Provenance(records, warnings, manifest_path)
