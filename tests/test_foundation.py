import json
from pathlib import Path

import pytest

from videosplitguard.audit import audit
from videosplitguard.cli import main
from videosplitguard.dataset import load_dataset
from videosplitguard.models import DatasetError
from videosplitguard.report import render_html


@pytest.fixture
def dataset(tmp_path):
    for split in ("train", "val", "test"):
        (tmp_path / split).mkdir()
    # Byte fixtures exercise hashing only; real JPEGs are tested by verify_public_datasets.py.
    (tmp_path / "train/a.jpg").write_bytes(b"first")
    (tmp_path / "val/b.JPG").write_bytes(b"second")
    (tmp_path / "test/c.png").write_bytes(b"third")
    path = tmp_path / "dataset.yaml"
    path.write_text("path: .\ntrain: train\nval: val\ntest: test\n", encoding="utf-8")
    return path


def test_disjoint_and_unknown_provenance(dataset):
    report = audit(dataset)
    assert report["summary"]["confirmed_exact_groups"] == 0
    assert report["summary"]["split_memberships"] == {"train": 1, "val": 1, "test": 1}
    assert report["provenance"]["video"]["missing_memberships"] == 3
    assert report["checks"]["source_video"] == "NOT VERIFIED"
    assert report["status"] == "NOT VERIFIED"


def test_renamed_copy_across_three_splits(dataset):
    for path in ("val/b.JPG", "test/c.png"):
        (dataset.parent / path).write_bytes(b"first")
    report = audit(dataset)
    assert report["summary"]["confirmed_exact_groups"] == 1
    assert report["summary"]["affected_memberships"] == 3
    assert report["findings"][0]["splits"] == ["test", "train", "val"]


def test_same_directory_in_both_splits(dataset):
    dataset.write_text("train: train\nval: train\n", encoding="utf-8")
    report = audit(dataset)
    assert report["summary"]["unique_files"] == 1
    assert report["summary"]["confirmed_exact_groups"] == 1
    assert report["summary"]["shared_path_groups"] == 1
    assert report["findings"][0]["evidence"] == "confirmed_shared_path"


def test_shared_path_stays_visible_in_group_with_renamed_copy(dataset):
    (dataset.parent / "val/b.JPG").write_bytes(b"first")
    dataset.write_text("train: train\nval: [train, val]\n", encoding="utf-8")
    report = audit(dataset)
    assert report["summary"]["confirmed_exact_groups"] == 1
    assert report["summary"]["shared_path_groups"] == 1
    assert report["summary"]["shared_path_count"] == 1
    assert report["findings"][0]["evidence"] == "confirmed_bytes"
    assert report["findings"][0]["shared_paths"] == ["train/a.jpg"]
    assert "Shared across splits" in render_html(report)


def test_within_split_duplicates_are_not_leakage(dataset):
    (dataset.parent / "train/copy.jpg").write_bytes(b"first")
    assert audit(dataset)["findings"] == []


def test_lists_bom_and_cwd_independence(dataset, monkeypatch, tmp_path):
    lists = tmp_path / "lists"
    lists.mkdir()
    (lists / "train.txt").write_text("../train/a.jpg\n../train/a.jpg\n", encoding="utf-8-sig")
    dataset.write_text("train: [lists/train.txt, train]\nval: val\n", encoding="utf-8-sig")
    monkeypatch.chdir(tmp_path.parent)
    result = load_dataset(dataset)
    assert len(result.samples) == 2
    assert any("deduplicated" in w for w in result.warnings)


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        "train: missing\nval: val",
        "train: []\nval: val",
        "train: 42\nval: val",
        "train: train",
        "train: train\nval: empty",
        "path: 42\ntrain: train\nval: val",
        "!!python/object/apply:os.system ['echo unsafe']",
        "train: [null]\nval: val",
        "train: train\ntrain: val\nval: val",
    ],
)
def test_invalid_input_fails_closed(dataset, content):
    (dataset.parent / "empty").mkdir()
    dataset.write_text(content, encoding="utf-8")
    with pytest.raises(DatasetError):
        load_dataset(dataset)


def test_download_is_not_executed(dataset):
    with dataset.open("a", encoding="utf-8") as stream:
        stream.write("download: 'raise RuntimeError()'\n")
    assert any("ignored" in w for w in load_dataset(dataset).warnings)


def test_root_override(dataset, tmp_path):
    elsewhere = tmp_path / "configs"
    elsewhere.mkdir()
    config = elsewhere / "data.yaml"
    config.write_text("path: nonexistent\ntrain: train\nval: val\n", encoding="utf-8")
    assert len(load_dataset(config, dataset.parent).samples) == 2


def test_missing_manifest_image(dataset):
    (dataset.parent / "train.txt").write_text("missing.jpg\n", encoding="utf-8")
    dataset.write_text("train: train.txt\nval: val\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="Invalid image"):
        load_dataset(dataset)


def test_html_escapes_untrusted_content(dataset):
    report = audit(dataset)
    report["warnings"].append('<script>alert("x")</script>')
    rendered = render_html(report)
    assert "<script" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "https://" not in rendered
    assert "NOT VERIFIED" in rendered


def test_cli_reports_exit_codes_and_no_overwrite(dataset, tmp_path):
    output = tmp_path / "report"
    assert main(["scan", str(dataset), "--output", str(output)]) == 0
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["schema_version"] == "0.2"
    assert (output / "report.html").is_file()
    assert main(["scan", str(dataset), "--output", str(output)]) == 2
    (dataset.parent / "val/b.JPG").write_bytes(b"first")
    assert main(["scan", str(dataset), "--output", str(tmp_path / "leak")]) == 1
    assert (
        main(["scan", str(dataset), "--output", str(tmp_path / "allowed"), "--fail-on", "none"])
        == 0
    )


def test_cli_missing_file_does_not_write_report(tmp_path):
    output = tmp_path / "report"
    assert main(["scan", str(tmp_path / "missing.yaml"), "--output", str(output)]) == 2
    assert not output.exists()


def test_findings_are_deterministic(dataset):
    (dataset.parent / "val/b.JPG").write_bytes(b"first")
    assert audit(dataset)["findings"] == audit(dataset)["findings"]


def test_relative_backslashes(dataset):
    dataset.write_text("train: 'train\\a.jpg'\nval: 'val\\b.JPG'\n", encoding="utf-8")
    assert len(load_dataset(dataset).samples) == 2


def test_hash_failure_is_not_clean(dataset, monkeypatch, tmp_path):
    from videosplitguard.detectors import exact

    def denied(path: Path):
        raise PermissionError("denied")

    monkeypatch.setattr(exact, "sha256_file", denied)
    assert main(["scan", str(dataset), "--output", str(tmp_path / "denied")]) == 2
