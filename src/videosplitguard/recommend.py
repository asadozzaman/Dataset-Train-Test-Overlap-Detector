"""Read-only grouping and deterministic approximate split assignment."""

import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from videosplitguard.models import Dataset, Provenance


def recommend_splits(dataset: Dataset, provenance: Provenance, hashes: dict[Path, str]) -> dict:
    paths = sorted(hashes)
    parent = {path: path for path in paths}

    def find(path: Path) -> Path:
        while parent[path] != path:
            parent[path] = parent[parent[path]]
            path = parent[path]
        return path

    def union(left: Path, right: Path) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[max(a, b)] = min(a, b)

    def union_groups(keyed_paths: dict[str, list[Path]]) -> None:
        for members in keyed_paths.values():
            for path in members[1:]:
                union(members[0], path)

    by_digest: dict[str, list[Path]] = defaultdict(list)
    by_video: dict[str, list[Path]] = defaultdict(list)
    by_session: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        by_digest[hashes[path]].append(path)
        record = provenance.records.get(path)
        if record and record.evidence == "verified":
            if record.video_id:
                by_video[record.video_id].append(path)
            if record.session_id:
                by_session[record.session_id].append(path)
    for groups in (by_digest, by_video, by_session):
        union_groups(groups)

    components: dict[Path, list[Path]] = defaultdict(list)
    for path in paths:
        components[find(path)].append(path)
    ordered = sorted(components.values(), key=lambda members: (-len(members), members[0]))
    current: dict[Path, set[str]] = defaultdict(set)
    for sample in dataset.samples:
        current[sample.path].add(sample.split)
    split_counts = Counter(sample.split for sample in dataset.samples)
    splits = [split for split in ("train", "val", "test") if split in split_counts]
    total_memberships = sum(split_counts.values())
    target = {split: len(paths) * split_counts[split] / total_memberships for split in splits}
    proposed = Counter({split: 0 for split in splits})
    assignments = {}
    component_ids = {}
    for members in ordered:
        size = len(members)

        def score(
            split: str, group_size: int = size, group: tuple[Path, ...] = tuple(members)
        ) -> tuple:
            projected = sum(
                abs(proposed[name] + (group_size if name == split else 0) - target[name])
                for name in splits
            )
            existing = sum(split in current[path] for path in group)
            return (round(projected, 9), -existing, splits.index(split))

        chosen = min(splits, key=score)
        proposed[chosen] += size
        component_id = hashlib.sha256(
            "\0".join(path.as_posix() for path in members).encode("utf-8")
        ).hexdigest()[:16]
        for path in members:
            assignments[path] = chosen
            component_ids[path] = component_id

    def display(path: Path) -> str:
        try:
            return path.relative_to(dataset.root).as_posix()
        except ValueError:
            return path.as_posix()

    rows = [
        {
            "path": display(path),
            "current_splits": ";".join(sorted(current[path])),
            "proposed_split": assignments[path],
            "component_id": component_ids[path],
        }
        for path in paths
    ]
    empty_splits = [split for split in splits if proposed[split] == 0]
    warnings = []
    if empty_splits:
        warnings.append(
            "This proposal leaves configured split(s) empty: "
            + ", ".join(empty_splits)
            + ". Review the grouping and split targets before use."
        )
    largest_component = max(len(members) for members in ordered)
    if largest_component > max(target.values()):
        warnings.append(
            f"The largest indivisible group has {largest_component} images, exceeding every "
            "target split size. Exact target ratios are impossible with these groups."
        )
    return {
        "status": "REVIEW REQUIRED" if warnings else "PROPOSED",
        "file": "suggested_splits.csv",
        "component_count": len(components),
        "target_counts": {split: round(target[split], 2) for split in splits},
        "proposed_counts": {split: proposed[split] for split in splits},
        "deviation_counts": {split: round(proposed[split] - target[split], 2) for split in splits},
        "empty_splits": empty_splits,
        "warnings": warnings,
        "removed_memberships": sum(
            sample.split != assignments[sample.path] for sample in dataset.samples
        ),
        "new_assignments": sum(assignments[path] not in current[path] for path in paths),
        "rows": rows,
        "notes": [
            "Proposal only: no images, labels, or dataset YAML are changed.",
            "Exact-byte groups and verified video/session IDs stay in one proposed split.",
            "Unverified source IDs are ignored for grouping; review them before applying.",
            "Ratios are approximate; large groups may make targets impossible.",
            "Class balance and label distribution are not evaluated.",
        ],
    }
