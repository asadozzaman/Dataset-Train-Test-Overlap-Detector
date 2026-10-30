"""Deterministic orchestration and the versioned JSON report contract."""

from collections import Counter, defaultdict
from pathlib import Path

from videosplitguard import PROJECT_NAME, __version__
from videosplitguard.dataset import load_dataset
from videosplitguard.detectors.exact import detect_exact, hash_all
from videosplitguard.detectors.groups import detect_group_overlap
from videosplitguard.detectors.near import (
    MAX_FINDINGS,
    MAX_IMAGES,
    MAX_PIXELS_PER_IMAGE,
    detect_near,
)
from videosplitguard.models import Finding, Provenance, Sample
from videosplitguard.provenance import load_provenance
from videosplitguard.recommend import recommend_splits as make_recommendation


def _coverage(samples: tuple[Sample, ...], provenance: Provenance, field: str) -> dict:
    verified = asserted = 0
    for sample in samples:
        record = provenance.records.get(sample.path)
        if record and getattr(record, field):
            asserted += 1
            verified += record.evidence == "verified"
    return {
        "verified_memberships": verified,
        "unverified_memberships": asserted - verified,
        "missing_memberships": len(samples) - asserted,
    }


def _group_status(findings: tuple[Finding, ...], coverage: dict) -> str:
    if any(f.evidence == "verified_metadata" for f in findings):
        return "FAIL"
    if coverage["verified_memberships"] and not (
        coverage["unverified_memberships"] or coverage["missing_memberships"]
    ):
        return "PASS"
    return "NOT VERIFIED"


def audit(
    yaml_path: Path,
    root_override: Path | None = None,
    provenance_path: Path | None = None,
    near_duplicates: bool = False,
    near_threshold: int = 6,
    recommend_splits: bool = False,
) -> dict:
    dataset = load_dataset(yaml_path, root_override)
    provenance = load_provenance(dataset, provenance_path)
    hashes = hash_all(dataset.samples)
    exact = detect_exact(dataset.samples, hashes)
    shared_paths = {}
    for finding in exact:
        memberships: dict[Path, set[str]] = defaultdict(set)
        for sample in finding.members:
            memberships[sample.path].add(sample.split)
        shared_paths[finding.group_id] = sorted(
            path for path, splits in memberships.items() if len(splits) > 1
        )
    videos = detect_group_overlap(dataset.samples, provenance, "video_id", "source_video_overlap")
    sessions = detect_group_overlap(
        dataset.samples, provenance, "session_id", "recording_session_overlap"
    )
    near = detect_near(dataset.samples, exact, near_threshold) if near_duplicates else None
    split_plan = make_recommendation(dataset, provenance, hashes) if recommend_splits else None
    findings = exact + videos + sessions + (near.findings if near else ())
    video_coverage = _coverage(dataset.samples, provenance, "video_id")
    session_coverage = _coverage(dataset.samples, provenance, "session_id")
    checks = {
        "exact_overlap": "FAIL" if exact else "PASS",
        "source_video": _group_status(videos, video_coverage),
        "recording_session": _group_status(sessions, session_coverage),
    }
    status = (
        "FAIL"
        if "FAIL" in checks.values()
        else "PASS"
        if all(value == "PASS" for value in checks.values())
        else "NOT VERIFIED"
    )
    if status == "PASS" and near and near.status == "NOT VERIFIED":
        status = "NOT VERIFIED"

    def display_path(path: Path) -> str:
        try:
            return path.relative_to(dataset.root).as_posix()
        except ValueError:
            return path.as_posix()

    def member_data(finding: Finding, sample: Sample) -> dict:
        data = {"path": display_path(sample.path), "split": sample.split}
        if finding.kind == "near_duplicate_candidate":
            data["sha256"] = hashes[sample.path]
        if finding.kind in {"source_video_overlap", "recording_session_overlap"}:
            record = provenance.records[sample.path]
            data["evidence"] = record.evidence
            data["source_ref"] = record.source_ref
        return data

    confirmed = tuple(
        f
        for f in findings
        if f.evidence.startswith("confirmed_") or f.evidence == "verified_metadata"
    )
    candidate = tuple(
        f for f in findings if f.evidence in {"unverified_metadata", "perceptual_dhash"}
    )
    recommendations = []
    if exact:
        recommendations.append(
            "Review each exact image group; keep a shared image in one evaluation partition "
            "unless the overlap is intentional and documented."
        )
    if any(f.evidence == "verified_metadata" for f in videos):
        recommendations.append(
            "Keep every frame from each affected source video in one split; regenerate "
            "splits from verified video IDs."
        )
    if any(f.evidence == "verified_metadata" for f in sessions):
        recommendations.append(
            "Keep each affected recording session in one split, including all its videos."
        )
    if any(f.evidence == "unverified_metadata" for f in candidate):
        recommendations.append(
            "Review candidate source groups against export logs or recording manifests "
            "before changing splits."
        )
    if near and near.findings:
        recommendations.append(
            "Inspect perceptual-hash candidates visually and check their source records; "
            "similarity alone does not establish shared video or session origin."
        )
    if any(
        coverage["missing_memberships"] or coverage["unverified_memberships"]
        for coverage in (video_coverage, session_coverage)
    ):
        recommendations.append(
            "Provide a provenance CSV with dataset-relative image paths, source video "
            "and session IDs, and reviewed source references to verify source separation."
        )
    if not recommendations:
        recommendations.append(
            "Keep the provenance manifest with the dataset and rerun this audit after data changes."
        )
    return {
        "schema_version": "0.2",
        "tool": {"name": PROJECT_NAME, "version": __version__},
        "status": status,
        "dataset": {
            "yaml": dataset.yaml_path.as_posix(),
            "root": dataset.root.as_posix(),
            "provenance_csv": provenance.manifest_path.as_posix()
            if provenance.manifest_path
            else None,
        },
        "checks": checks,
        "summary": {
            "split_memberships": dict(sorted(Counter(s.split for s in dataset.samples).items())),
            "unique_files": len({s.path for s in dataset.samples}),
            "confirmed_exact_groups": len(exact),
            "shared_path_groups": sum(bool(paths) for paths in shared_paths.values()),
            "shared_path_count": sum(len(paths) for paths in shared_paths.values()),
            "confirmed_video_groups": sum(f.evidence == "verified_metadata" for f in videos),
            "confirmed_session_groups": sum(f.evidence == "verified_metadata" for f in sessions),
            "candidate_groups": len(candidate),
            "near_duplicate_candidates": len(near.findings) if near else 0,
            "affected_memberships": len({s for f in findings for s in f.members}),
            "confirmed_affected_memberships": len({s for f in confirmed for s in f.members}),
            "candidate_affected_memberships": len({s for f in candidate for s in f.members}),
        },
        "provenance": {
            "video": video_coverage,
            "session": session_coverage,
            "source": "user_supplied_csv" if provenance.manifest_path else "none",
            "evidence_note": (
                "Verified metadata means the CSV row cites a reviewed source reference; "
                "the tool cannot independently authenticate that reference."
            ),
        },
        "optional_checks": {
            "near_duplicates": {
                "status": near.status if near else "NOT REQUESTED",
                "threshold": near_threshold if near else None,
                "max_images": MAX_IMAGES,
                "max_findings": MAX_FINDINGS,
                "max_pixels_per_image": MAX_PIXELS_PER_IMAGE,
                "max_structural_comparisons": MAX_FINDINGS,
                "structural_comparisons": len(near.findings) if near else 0,
                "score_method": "ssim_grayscale_128_uniform7",
                "images_considered": near.images_considered if near else 0,
                "comparisons": near.comparisons if near else 0,
                "truncated": near.truncated if near else False,
                "reason": near.reason if near else None,
            }
        },
        "split_recommendations": split_plan,
        "findings": [
            {
                "kind": finding.kind,
                "status": "NOT VERIFIED"
                if finding.evidence in {"unverified_metadata", "perceptual_dhash"}
                else "FAIL",
                "evidence": finding.evidence,
                "group_id": finding.group_id,
                "splits": sorted({sample.split for sample in finding.members}),
                "members": [member_data(finding, sample) for sample in finding.members],
                **({"similarity": finding.similarity} if finding.similarity else {}),
                **(
                    {"shared_paths": [display_path(p) for p in shared_paths[finding.group_id]]}
                    if finding.kind == "exact_overlap"
                    else {}
                ),
            }
            for finding in findings
        ],
        "recommendations": recommendations,
        "warnings": list(dataset.warnings)
        + list(provenance.warnings)
        + ([near.reason] if near and near.reason else []),
        "limitations": [
            "Exact matching compares file bytes only; visual equivalence is not confirmed.",
            "Labels and image integrity are not validated; previews and similarity decode images.",
            "Perceptual dHash (when requested) yields review candidates, not source proof.",
            "SSIM appearance percentages are not leakage percentages or confidence. "
            "Resizing, grayscale conversion, lighting, crop and alignment affect scores; "
            "unrelated flat images may score highly. Low-information pairs need extra care.",
            "A PASS relies on complete, reviewed CSV assertions for video/session origin; "
            "it is not independent forensic proof of provenance.",
        ],
    }
