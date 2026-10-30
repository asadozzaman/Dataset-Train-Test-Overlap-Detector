"""Split proposals use verified groups and leave the input dataset unchanged."""

import csv

from videosplitguard.audit import audit
from videosplitguard.cli import main


def make_dataset(tmp_path):
    for split in ("train", "val", "test"):
        (tmp_path / split).mkdir()
    for name, payload in (
        ("train/a.jpg", b"a"),
        ("train/b.jpg", b"b"),
        ("val/c.jpg", b"c"),
        ("test/d.jpg", b"d"),
    ):
        (tmp_path / name).write_bytes(payload)
    yaml_path = tmp_path / "data.yaml"
    yaml_path.write_text("train: train\nval: val\ntest: test\n", encoding="utf-8")
    return yaml_path


def test_verified_session_group_stays_together_and_csv_is_read_only(tmp_path):
    yaml_path = make_dataset(tmp_path)
    provenance = tmp_path / "provenance.csv"
    provenance.write_text(
        "path,video_id,session_id,evidence,source_ref\n"
        "train/a.jpg,v1,s1,verified,synthetic-source\n"
        "val/c.jpg,v2,s1,verified,synthetic-source\n",
        encoding="utf-8",
    )
    originals = {path: path.read_bytes() for path in tmp_path.rglob("*.jpg")}
    first = audit(yaml_path, provenance_path=provenance, recommend_splits=True)
    second = audit(yaml_path, provenance_path=provenance, recommend_splits=True)
    assert first == second
    plan = first["split_recommendations"]
    rows = {row["path"]: row for row in plan["rows"]}
    assert rows["train/a.jpg"]["proposed_split"] == rows["val/c.jpg"]["proposed_split"]
    assert rows["train/a.jpg"]["component_id"] == rows["val/c.jpg"]["component_id"]
    assert sum(plan["proposed_counts"].values()) == 4
    output = tmp_path / "report"
    assert (
        main(
            [
                "audit",
                str(yaml_path),
                "--provenance",
                str(provenance),
                "--recommend-splits",
                "--output",
                str(output),
            ]
        )
        == 1
    )
    with (output / "suggested_splits.csv").open(encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    assert len(csv_rows) == 4
    assert {path: path.read_bytes() for path in originals} == originals
    assert yaml_path.read_text(encoding="utf-8") == "train: train\nval: val\ntest: test\n"


def test_within_split_exact_copies_are_grouped(tmp_path):
    yaml_path = make_dataset(tmp_path)
    (tmp_path / "train/e.jpg").write_bytes(b"a")
    report = audit(yaml_path, recommend_splits=True)
    assert report["summary"]["confirmed_exact_groups"] == 0
    rows = {row["path"]: row for row in report["split_recommendations"]["rows"]}
    assert rows["train/a.jpg"]["component_id"] == rows["train/e.jpg"]["component_id"]


def test_unverified_ids_do_not_constrain_proposal(tmp_path):
    yaml_path = make_dataset(tmp_path)
    provenance = tmp_path / "provenance.csv"
    provenance.write_text(
        "path,video_id,session_id,evidence,source_ref\n"
        "train/a.jpg,v1,s1,unverified,\n"
        "val/c.jpg,v1,s1,unverified,\n",
        encoding="utf-8",
    )
    report = audit(yaml_path, provenance_path=provenance, recommend_splits=True)
    assert report["summary"]["candidate_groups"] == 2
    assert report["split_recommendations"]["component_count"] == 4


def test_indivisible_group_discloses_empty_splits_and_ratio_difference(tmp_path, capsys):
    yaml_path = make_dataset(tmp_path)
    for image in tmp_path.rglob("*.jpg"):
        image.write_bytes(b"one indivisible group")
    report = audit(yaml_path, recommend_splits=True)
    plan = report["split_recommendations"]
    assert plan["status"] == "REVIEW REQUIRED"
    assert len(plan["empty_splits"]) == 2
    assert any("empty" in warning for warning in plan["warnings"])
    assert any("impossible" in warning for warning in plan["warnings"])
    assert sum(plan["proposed_counts"].values()) == 4
    for split in plan["target_counts"]:
        assert plan["deviation_counts"][split] == (
            plan["proposed_counts"][split] - plan["target_counts"][split]
        )
    assert (
        main(["audit", str(yaml_path), "--recommend-splits", "--output", str(tmp_path / "report")])
        == 1
    )
    assert "REVIEW REQUIRED" in capsys.readouterr().out
