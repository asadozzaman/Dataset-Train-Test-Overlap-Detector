"""Failures must not leave a successfully published analysis or erase existing output."""

from pathlib import Path

import pytest

from videosplitguard import report as reporting
from videosplitguard.audit import audit
from videosplitguard.cli import main


@pytest.fixture
def source(tmp_path):
    for split in ("train", "val"):
        (tmp_path / split).mkdir()
        (tmp_path / split / "image.jpg").write_bytes(split.encode())
    config = tmp_path / "data.yaml"
    config.write_text("train: train\nval: val\n", encoding="utf-8")
    return config


def test_render_failure_does_not_publish_partial_report(source, tmp_path, monkeypatch):
    output = tmp_path / "report"

    def unavailable(_):
        raise OSError("simulated HTML write failure")

    monkeypatch.setattr(reporting, "render_html", unavailable)
    assert main(["audit", str(source), "--output", str(output)]) == 2
    assert not output.exists()
    assert list(tmp_path.glob(".report-*.tmp")) == []


def test_publication_failure_rolls_back_html_and_csv(source, tmp_path, monkeypatch):
    output = tmp_path / "report"
    original = Path.replace

    def fail_json(path, destination):
        if path.name == "report.json":
            assert (output / "report.html").exists()
            assert (output / "suggested_splits.csv").exists()
            raise OSError("simulated publication failure")
        return original(path, destination)

    monkeypatch.setattr(Path, "replace", fail_json)
    assert main(["audit", str(source), "--output", str(output), "--recommend-splits"]) == 2
    assert not output.exists()
    assert list(tmp_path.glob(".report-*.tmp")) == []


def test_output_created_during_staging_is_preserved(source, tmp_path, monkeypatch):
    output = tmp_path / "report"
    original = reporting._write_artifacts

    def concurrent_output(report, stage):
        original(report, stage)
        output.mkdir()
        (output / "existing.txt").write_text("keep", encoding="utf-8")

    monkeypatch.setattr(reporting, "_write_artifacts", concurrent_output)
    with pytest.raises(FileExistsError):
        reporting.write_reports(audit(source), output)
    assert (output / "existing.txt").read_text(encoding="utf-8") == "keep"
    assert list(output.iterdir()) == [output / "existing.txt"]
    assert list(tmp_path.glob(".report-*.tmp")) == []


def test_json_is_published_last_and_outputs_are_deterministic(source, tmp_path, monkeypatch):
    original = Path.replace
    published = []

    def track(path, destination):
        published.append(path.name)
        return original(path, destination)

    monkeypatch.setattr(Path, "replace", track)
    result = audit(source, recommend_splits=True)
    for name in ("first", "second"):
        reporting.write_reports(result, tmp_path / name)
    assert published == ["report.html", "suggested_splits.csv", "report.json"] * 2
    for name in set(published):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
