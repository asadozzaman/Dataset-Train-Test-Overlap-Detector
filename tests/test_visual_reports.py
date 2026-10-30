"""Evidence reports carry bounded image previews and explicit source references."""

import base64
import io
import re
import shutil

from PIL import Image

from videosplitguard import previews
from videosplitguard.audit import audit
from videosplitguard.report import render_html, write_reports


def make_dataset(tmp_path):
    for split in ("train", "val"):
        (tmp_path / split).mkdir()
    image = Image.new("RGB", (800, 600), "#206090")
    image.save(tmp_path / "train/source.png")
    shutil.copyfile(tmp_path / "train/source.png", tmp_path / "val/renamed.png")
    config = tmp_path / "data.yaml"
    config.write_text("train: train\nval: val\n", encoding="utf-8")
    return config


def test_exact_overlap_has_two_embedded_images_and_original_references(tmp_path):
    config = make_dataset(tmp_path)
    report = audit(config)
    rendered = render_html(report)
    embedded = re.findall(r'<img src="data:image/jpeg;base64,([^\"]+)"', rendered)
    assert len(embedded) == 2
    assert embedded[0] == embedded[1]
    with Image.open(io.BytesIO(base64.b64decode(embedded[0]))) as thumbnail:
        assert thumbnail.format == "JPEG"
        assert thumbnail.width <= 384 and thumbnail.height <= 256
    assert (tmp_path / "train/source.png").as_uri() in rendered
    assert (tmp_path / "val/renamed.png").as_uri() in rendered
    assert 'class="image-label train">TRAIN' in rendered
    assert 'class="image-label val">VAL' in rendered
    assert "train/source.png" in rendered and "val/renamed.png" in rendered
    assert report["status"] == "FAIL"
    assert "data:image" not in str(report)


def test_preview_is_portable_deterministic_and_does_not_modify_sources(tmp_path):
    config = make_dataset(tmp_path)
    originals = {p: p.read_bytes() for p in tmp_path.rglob("*.png")}
    report = audit(config)
    first = render_html(report)
    assert first == render_html(report)
    output = tmp_path / "report"
    write_reports(report, output)
    assert (output / "report.html").read_text(encoding="utf-8") == first
    moved = tmp_path / "moved-report.html"
    shutil.copyfile(output / "report.html", moved)
    assert 'src="data:image/jpeg;base64,' in moved.read_text(encoding="utf-8")
    assert {p: p.read_bytes() for p in originals} == originals


def test_preview_selection_includes_other_split_before_training_extras():
    members = [{"path": f"train/{i}.png", "split": "train"} for i in range(12)]
    members.append({"path": "val/one.png", "split": "val"})
    selected = previews.select_members(members)
    assert len(selected) == previews.MAX_MEMBERS_PER_GROUP
    assert selected[1]["split"] == "val"


def test_large_group_keeps_all_references_and_shows_sampling_note(tmp_path):
    config = make_dataset(tmp_path)
    report = audit(config)
    report["findings"][0]["members"] = [
        {"path": f"train/image-{i}.png", "split": "train"} for i in range(10)
    ] + [{"path": "val/renamed.png", "split": "val"}]
    rendered = render_html(report)
    assert "Showing 8 of 11 memberships" in rendered
    assert "All 11 image references" in rendered
    assert "train/image-9.png" in rendered
    assert 'class="image-label val">VAL' in rendered


def test_corrupt_or_missing_image_does_not_change_confirmed_finding(tmp_path):
    config = make_dataset(tmp_path)
    (tmp_path / "train/source.png").write_bytes(b"invalid image bytes")
    shutil.copyfile(tmp_path / "train/source.png", tmp_path / "val/renamed.png")
    report = audit(config)
    (tmp_path / "val/renamed.png").unlink()
    output = tmp_path / "report"
    write_reports(report, output)
    rendered = (output / "report.html").read_text(encoding="utf-8")
    assert report["status"] == "FAIL"
    assert "Preview unavailable" in rendered
    assert "val/renamed.png" in rendered
    assert '<img src="' not in rendered


def test_decoding_and_embedding_budgets_are_enforced(tmp_path, monkeypatch):
    config = make_dataset(tmp_path)
    cache = previews.ImagePreviews(config.parent)
    monkeypatch.setattr(previews, "MAX_UNIQUE_IMAGES", 1)
    assert cache.get(tmp_path / "train/source.png").data_url
    assert "limit" in cache.get(tmp_path / "val/renamed.png").message
    monkeypatch.setattr(previews, "MAX_EMBEDDED_BYTES", 0)
    assert "budget" in cache.get(tmp_path / "train/source.png").message
    assert cache.omitted == 2


def test_metadata_gallery_does_not_claim_visual_identity(tmp_path):
    config = make_dataset(tmp_path)
    Image.new("RGB", (200, 100), "orange").save(tmp_path / "val/renamed.png")
    manifest = tmp_path / "sources.csv"
    manifest.write_text(
        "path,video_id,session_id,evidence,source_ref\n"
        "train/source.png,synthetic-v,synthetic-s,verified,test-only-reference\n"
        "val/renamed.png,synthetic-v,synthetic-s,verified,test-only-reference\n",
        encoding="utf-8",
    )
    report = audit(config, provenance_path=manifest)
    rendered = render_html(report)
    assert "Different frames need not look identical" in rendered
    assert "Grouping is based on the source records" in rendered
    assert "test-only-reference" in rendered
    assert rendered.count('<img src="data:image/jpeg;base64,') == 4
