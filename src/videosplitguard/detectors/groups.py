"""Group overlapping video/session IDs without upgrading unverified assertions."""

from collections import defaultdict

from videosplitguard.models import Finding, Provenance, Sample


def detect_group_overlap(
    samples: tuple[Sample, ...], provenance: Provenance, field: str, kind: str
) -> tuple[Finding, ...]:
    groups: dict[str, list[Sample]] = defaultdict(list)
    for sample in samples:
        record = provenance.records.get(sample.path)
        group_id = getattr(record, field) if record else None
        if group_id:
            groups[group_id].append(sample)
    findings = []
    for group_id, members in sorted(groups.items()):
        if len({member.split for member in members}) < 2:
            continue
        verified = tuple(
            member for member in members if provenance.records[member.path].evidence == "verified"
        )
        if len({member.split for member in verified}) >= 2:
            findings.append(Finding(kind, "verified_metadata", group_id, verified))
        # A separate candidate keeps any unverified membership out of the confirmed set.
        if len(verified) != len(members):
            findings.append(Finding(kind, "unverified_metadata", group_id, tuple(members)))
    return tuple(findings)
