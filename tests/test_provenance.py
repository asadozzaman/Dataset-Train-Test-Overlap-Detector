"""Synthetic source histories: these IDs are fixtures, not COCO provenance."""

import json

import pytest

from videosplitguard.audit import audit
from videosplitguard.cli import main
from videosplitguard.models import DatasetError
from videosplitguard.report import render_html


@pytest.fixture
def scene(tmp_path):
    for split, name, content in (
        ("train", "a.jpg", b"a"),
        ("train", "b.jpg", b"b"),
        ("val", "c.jpg", b"c"),
        ("test", "d.jpg", b"d"),
    ):
        folder = tmp_path / "images" / split
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(content)
    yaml_path = tmp_path / "data.yaml"
    yaml_path.write_text(
        "train: images/train\nval: images/val\ntest: images/test\n", encoding="utf-8"
    )
    csv_path = tmp_path / "provenance.csv"
    return yaml_path, csv_path


def write_csv(path, rows):
    path.write_text(
        "path,video_id,session_id,evidence,source_ref\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )


def test_verified_video_and_session_overlap_are_separate_findings(scene):
    yaml_path, csv_path = scene
    write_csv(
        csv_path,
        [
            "images/train/a.jpg,video-1,session-1,verified,synthetic-export-v1",
            "images/train/b.jpg,video-2,session-1,verified,synthetic-export-v1",
            "images/val/c.jpg,video-1,session-1,verified,synthetic-export-v1",
            "images/test/d.jpg,video-3,session-3,verified,synthetic-export-v1",
        ],
    )
    report = audit(yaml_path, provenance_path=csv_path)
    assert report["status"] == "FAIL"
    assert report["checks"] == {
        "exact_overlap": "PASS",
        "source_video": "FAIL",
        "recording_session": "FAIL",
    }
    assert report["summary"]["confirmed_video_groups"] == 1
    assert report["summary"]["confirmed_session_groups"] == 1
    assert report["summary"]["affected_memberships"] == 3
    assert any("Provide a provenance CSV" in rec for rec in report["recommendations"]) is False
    video = next(f for f in report["findings"] if f["kind"] == "source_video_overlap")
    session = next(f for f in report["findings"] if f["kind"] == "recording_session_overlap")
    assert {m["path"] for m in video["members"]} == {"images/train/a.jpg", "images/val/c.jpg"}
    assert {m["path"] for m in session["members"]} == {
        "images/train/a.jpg",
        "images/train/b.jpg",
        "images/val/c.jpg",
    }
    assert all(m["source_ref"] == "synthetic-export-v1" for m in session["members"])
    assert any("session" in recommendation for recommendation in report["recommendations"])


def test_complete_reviewed_provenance_can_pass(scene):
    yaml_path, csv_path = scene
    write_csv(
        csv_path,
        [
            "images/train/a.jpg,video-1,session-1,verified,synthetic-record",
            "images/train/b.jpg,video-2,session-1,verified,synthetic-record",
            "images/val/c.jpg,video-3,session-2,verified,synthetic-record",
            "images/test/d.jpg,video-4,session-3,verified,synthetic-record",
        ],
    )
    report = audit(yaml_path, provenance_path=csv_path)
    assert report["status"] == "PASS"
    assert report["findings"] == []
    assert set(report["checks"].values()) == {"PASS"}
    assert report["provenance"]["video"]["verified_memberships"] == 4


def test_partial_metadata_remains_not_verified(scene):
    yaml_path, csv_path = scene
    write_csv(
        csv_path,
        [
            "images/train/a.jpg,video-1,session-1,verified,synthetic-record",
            "images/val/c.jpg,video-2,,verified,synthetic-record",
        ],
    )
    report = audit(yaml_path, provenance_path=csv_path)
    assert report["status"] == "NOT VERIFIED"
    assert report["checks"]["exact_overlap"] == "PASS"
    assert report["provenance"]["video"]["missing_memberships"] == 2
    assert report["provenance"]["session"]["missing_memberships"] == 3
    assert any("Provide a provenance CSV" in r for r in report["recommendations"])


def test_unverified_matching_id_is_candidate(scene, tmp_path):
    yaml_path, csv_path = scene
    write_csv(
        csv_path,
        [
            "images/train/a.jpg,video-1,session-1,unverified,",
            "images/val/c.jpg,video-1,session-1,unverified,",
        ],
    )
    report = audit(yaml_path, provenance_path=csv_path)
    assert report["status"] == "NOT VERIFIED"
    assert report["summary"]["candidate_groups"] == 2
    assert report["summary"]["confirmed_video_groups"] == 0
    assert all(f["status"] == "NOT VERIFIED" for f in report["findings"])
    assert (
        main(
            [
                "audit",
                str(yaml_path),
                "--provenance",
                str(csv_path),
                "--output",
                str(tmp_path / "candidate-default"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "audit",
                str(yaml_path),
                "--provenance",
                str(csv_path),
                "--output",
                str(tmp_path / "candidate-any"),
                "--fail-on",
                "any",
            ]
        )
        == 1
    )


def test_mixed_evidence_does_not_upgrade_unverified_rows(scene):
    yaml_path, csv_path = scene
    write_csv(
        csv_path,
        [
            "images/train/a.jpg,video-1,session-1,verified,synthetic-record",
            "images/val/c.jpg,video-1,session-1,unverified,",
        ],
    )
    report = audit(yaml_path, provenance_path=csv_path)
    assert report["summary"]["confirmed_video_groups"] == 0
    assert report["summary"]["candidate_groups"] == 2
    assert report["status"] == "NOT VERIFIED"


def test_verified_subset_and_candidate_are_distinct(scene):
    yaml_path, csv_path = scene
    write_csv(
        csv_path,
        [
            "images/train/a.jpg,video-1,session-1,verified,synthetic-record",
            "images/val/c.jpg,video-1,session-1,verified,synthetic-record",
            "images/test/d.jpg,video-1,session-1,unverified,",
        ],
    )
    report = audit(yaml_path, provenance_path=csv_path)
    video_findings = [f for f in report["findings"] if f["kind"] == "source_video_overlap"]
    assert len(video_findings) == 2
    confirmed = next(f for f in video_findings if f["status"] == "FAIL")
    assert len(confirmed["members"]) == 2
    assert {m["split"] for m in confirmed["members"]} == {"train", "val"}
    assert report["status"] == "FAIL"
    assert any("Provide a provenance CSV" in rec for rec in report["recommendations"])


def test_group_within_single_split_is_not_finding(scene):
    yaml_path, csv_path = scene
    write_csv(
        csv_path,
        [
            "images/train/a.jpg,video-1,session-1,verified,synthetic-record",
            "images/train/b.jpg,video-1,session-1,verified,synthetic-record",
        ],
    )
    assert audit(yaml_path, provenance_path=csv_path)["findings"] == []


@pytest.mark.parametrize(
    "rows,pattern",
    [
        (["images/train/a.jpg,v,s,verified,"], "requires source_ref"),
        (["images/train/a.jpg,v,s,maybe,ref"], "Evidence must"),
        (
            ["images/train/a.jpg,v,s,verified,ref", "images/train/a.jpg,v,s,verified,ref"],
            "Duplicate provenance path",
        ),
        (["../outside.jpg,v,s,verified,ref"], "escapes dataset root"),
        (
            ["images/train/a.jpg,v,s1,verified,ref", "images/val/c.jpg,v,s2,verified,ref"],
            "conflicting session IDs",
        ),
        (["images/train/a.jpg,v,s,verified,ref,extra"], "Extra CSV fields"),
        (["images/train/a.jpg,v,s,unverified"], "Missing CSV fields"),
    ],
)
def test_bad_provenance_fails_closed(scene, rows, pattern):
    yaml_path, csv_path = scene
    write_csv(csv_path, rows)
    with pytest.raises(DatasetError, match=pattern):
        audit(yaml_path, provenance_path=csv_path)


def test_unused_manifest_rows_warn(scene):
    yaml_path, csv_path = scene
    write_csv(csv_path, ["images/train/absent.jpg,v,s,unverified,"])
    report = audit(yaml_path, provenance_path=csv_path)
    assert report["status"] == "NOT VERIFIED"
    assert any("not present" in warning for warning in report["warnings"])


def test_report_determinism_and_html_escape(scene, tmp_path):
    yaml_path, csv_path = scene
    write_csv(
        csv_path,
        [
            "images/train/a.jpg,video-1,session-1,verified,<script>alert(1)</script>",
            "images/val/c.jpg,video-1,session-1,verified,<script>alert(1)</script>",
        ],
    )
    first = audit(yaml_path, provenance_path=csv_path)
    second = audit(yaml_path, provenance_path=csv_path)
    assert json.dumps(first, indent=2) == json.dumps(second, indent=2)
    assert render_html(first) == render_html(second)
    assert "<script>" not in render_html(first)
    assert "&lt;script&gt;" in render_html(first)
    out = tmp_path / "report"
    assert main(["audit", str(yaml_path), "--provenance", str(csv_path), "--output", str(out)]) == 1
    assert json.loads((out / "report.json").read_text(encoding="utf-8")) == first
    assert "Recommended next steps" in (out / "report.html").read_text(encoding="utf-8")


def test_missing_manifest_is_error_without_report(scene, tmp_path):
    yaml_path, _ = scene
    output = tmp_path / "out"
    assert (
        main(
            [
                "audit",
                str(yaml_path),
                "--provenance",
                str(tmp_path / "missing.csv"),
                "--output",
                str(output),
            ]
        )
        == 2
    )
    assert not output.exists()
