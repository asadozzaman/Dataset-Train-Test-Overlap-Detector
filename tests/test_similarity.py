"""Opt-in candidate checks on real decodable images and a hard size bound."""

import shutil

import pytest

from videosplitguard.audit import audit
from videosplitguard.cli import main

PIL = pytest.importorskip("PIL.Image")
np = pytest.importorskip("numpy")


def make_dataset(tmp_path):
    for split in ("train", "val"):
        (tmp_path / split).mkdir()
    yaml_path = tmp_path / "data.yaml"
    yaml_path.write_text("train: train\nval: val\n", encoding="utf-8")
    return yaml_path


def patterned_image():
    image = PIL.new("RGB", (96, 96), "#203050")
    for x in range(48, 96):
        for y in range(96):
            image.putpixel((x, y), (230, 190, 90))
    return image


def test_reencoded_visual_candidate_is_not_confirmed(tmp_path):
    yaml_path = make_dataset(tmp_path)
    image = patterned_image()
    image.save(tmp_path / "train/a.png")
    image.save(tmp_path / "val/b.jpg", quality=96)
    report = audit(yaml_path, near_duplicates=True, near_threshold=8)
    assert report["summary"]["confirmed_exact_groups"] == 0
    assert report["summary"]["near_duplicate_candidates"] == 1
    assert report["findings"][0]["status"] == "NOT VERIFIED"
    assert report["findings"][0]["evidence"] == "perceptual_dhash"
    assert report["optional_checks"]["near_duplicates"]["comparisons"] == 1
    assert report["status"] == "NOT VERIFIED"
    score = report["findings"][0]["similarity"]
    assert score["structural_similarity_percent"] > 95
    assert score["dhash_distance"] <= 8
    assert score["method"] == "ssim_grayscale_128_uniform7"
    members = report["findings"][0]["members"]
    assert len(members[0]["sha256"]) == 64
    assert members[0]["sha256"] != members[1]["sha256"]
    assert report["optional_checks"]["near_duplicates"]["structural_comparisons"] == 1


def test_exact_group_not_repeated_as_near_candidate(tmp_path):
    yaml_path = make_dataset(tmp_path)
    patterned_image().save(tmp_path / "train/a.png")
    shutil.copyfile(tmp_path / "train/a.png", tmp_path / "val/b.png")
    report = audit(yaml_path, near_duplicates=True)
    assert report["summary"]["confirmed_exact_groups"] == 1
    assert report["summary"]["near_duplicate_candidates"] == 0


def test_similarity_limit_skips_without_claiming_clear(tmp_path):
    yaml_path = make_dataset(tmp_path)
    for index in range(2001):
        split = "train" if index % 2 else "val"
        (tmp_path / split / f"{index}.jpg").write_bytes(b"not decoded")
    report = audit(yaml_path, near_duplicates=True)
    near = report["optional_checks"]["near_duplicates"]
    assert near["status"] == "NOT VERIFIED"
    assert near["images_considered"] == 0
    assert near["comparisons"] == 0
    assert "limit" in near["reason"]


def test_bad_threshold_is_input_error(tmp_path):
    yaml_path = make_dataset(tmp_path)
    patterned_image().save(tmp_path / "train/a.png")
    patterned_image().save(tmp_path / "val/b.png")
    assert (
        main(
            [
                "audit",
                str(yaml_path),
                "--output",
                str(tmp_path / "report"),
                "--near-duplicates",
                "--near-threshold",
                "65",
            ]
        )
        == 2
    )
    assert not (tmp_path / "report").exists()


def test_candidate_output_cap_is_explicit(tmp_path):
    yaml_path = make_dataset(tmp_path)
    for index in range(50):
        split = "train" if index < 25 else "val"
        # Distinct byte content, same uniform-image dHash.
        PIL.new("RGB", (12, 12), (index, index, index)).save(tmp_path / split / f"{index}.png")
    report = audit(yaml_path, near_duplicates=True)
    near = report["optional_checks"]["near_duplicates"]
    assert near["truncated"] is True
    assert near["status"] == "NOT VERIFIED"
    assert report["summary"]["near_duplicate_candidates"] == 500
    assert near["comparisons"] <= 501
    assert near["structural_comparisons"] == 500
    assert all(f["similarity"]["low_information"] for f in report["findings"])


def test_ssim_matches_independent_window_reference():
    from videosplitguard.similarity import structural_similarity

    x = np.random.default_rng(47).integers(0, 256, (128, 128)).astype(float)
    y = np.clip(x * 0.87 + 12, 0, 255)
    # Independent, direct-window calculation validates the integral-image implementation.
    scores = []
    for row in range(122):
        for col in range(122):
            a, b = x[row : row + 7, col : col + 7], y[row : row + 7, col : col + 7]
            u, v = a.mean(), b.mean()
            covariance = ((a - u) * (b - v)).sum() / 48
            scores.append(
                ((2 * u * v + 6.5025) * (2 * covariance + 58.5225))
                / ((u * u + v * v + 6.5025) * (a.var(ddof=1) + b.var(ddof=1) + 58.5225))
            )
    assert structural_similarity(x, y) == pytest.approx(np.mean(scores), abs=1e-10)


def test_ssim_identity_symmetry_and_negative_score():
    from videosplitguard.similarity import score_pair, structural_similarity

    x = np.random.default_rng(3).integers(0, 256, (128, 128), dtype=np.uint8)
    y = 255 - x
    assert structural_similarity(x, x) == pytest.approx(1)
    assert structural_similarity(x, y) == pytest.approx(structural_similarity(y, x))
    score = score_pair(x, y, 64)
    assert score["ssim"] < 0
    assert score["structural_similarity_percent"] == 0
    assert score["hash_agreement_percent"] == 0


def test_low_detail_is_disclosed_even_when_score_is_high():
    from videosplitguard.similarity import score_pair

    score = score_pair(np.full((128, 128), 150), np.full((128, 128), 155), 0)
    assert score["structural_similarity_percent"] > 99
    assert score["low_information"] is True
    assert "not leakage probability" in score["note"]


def test_scores_are_in_json_html_and_repeatable(tmp_path):
    from videosplitguard.report import render_html

    config = make_dataset(tmp_path)
    patterned_image().save(tmp_path / "train/reference.png")
    patterned_image().save(tmp_path / "val/observation.jpg", quality=93)
    first = audit(config, near_duplicates=True, near_threshold=8)
    assert audit(config, near_duplicates=True, near_threshold=8) == first
    html = render_html(first)
    score = first["findings"][0]["similarity"]
    assert f"{score['structural_similarity_percent']:.2f}%" in html
    assert "Structural similarity (SSIM)" in html
    assert "appearance score, not leakage probability" in html
    assert "reference.png" in html and "observation.jpg" in html


def test_missing_numpy_is_an_actionable_input_error(monkeypatch):
    import builtins

    from videosplitguard.models import DatasetError
    from videosplitguard.similarity import require_numpy

    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "numpy":
            raise ImportError("test missing extra")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(DatasetError, match=r"install videosplitguard\[similarity\]"):
        require_numpy()


def test_pillow_decoding_limit_is_a_readable_cli_error(tmp_path, monkeypatch, capsys):
    yaml_path = make_dataset(tmp_path)
    patterned_image().save(tmp_path / "train/a.png")
    patterned_image().save(tmp_path / "val/b.png")
    monkeypatch.setattr(PIL, "MAX_IMAGE_PIXELS", 1)
    output = tmp_path / "report"
    assert main(["audit", str(yaml_path), "--near-duplicates", "--output", str(output)]) == 2
    assert "safe decoding limit" in capsys.readouterr().err
    assert not output.exists()
