"""Build a portable showcase from audited official COCO archives kept outside Git."""

import argparse
import base64
import copy
import hashlib
import html
import io
import json
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from PIL import Image, ImageOps

from videosplitguard import PROJECT_NAME, __version__
from videosplitguard.audit import audit
from videosplitguard.report import render_html

EXPECTED_DIGESTS = {
    "coco8": "54c67fe9ef88313e021ec0e92b73c200167bb0a86633e8df8658d832cca828c9",
    "coco128": "61e5e3028863d8ffc3b81d6a514603954889f0edd5e4b44c4ce60b2da99aeb8e",
}
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def thumbnail(path: Path) -> str:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((640, 480), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def public_report(
    result: dict, root: Path, config: Path, name: str, output: Path, note: str
) -> dict:
    public = copy.deepcopy(result)
    public["dataset"] = {"yaml": f"{name}.yaml", "root": name, "provenance_csv": None}
    public["warnings"].insert(0, note)
    displayed = copy.deepcopy(result)
    displayed["warnings"].insert(0, note)
    html = render_html(displayed)
    html = re.sub(
        r'<a class="source-link" href="file:[^"]*"[^>]*>Open original image</a>',
        '<span class="source-link">Image filename shown above</span>',
        html,
    )
    html = html.replace(root.as_posix(), name).replace(config.as_posix(), f"{name}.yaml")
    (output / "reports" / f"{name}.html").write_text(html, encoding="utf-8")
    (output / "reports" / f"{name}.json").write_text(
        json.dumps(public, indent=2) + "\n", encoding="utf-8"
    )
    return public


def build(output: Path, archives: Path, github_url: str | None = None) -> dict:
    """No external service is needed; evidence is calculated by the real engine."""
    if github_url and not re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+/?", github_url):
        raise ValueError("--github-url must be a GitHub repository URL")
    # Only the generated site directory is written. Never remove an existing directory.
    output.mkdir(parents=True, exist_ok=False)
    (output / "reports").mkdir()
    data = {"name": PROJECT_NAME, "version": __version__, "github_url": github_url, "datasets": {}}
    with TemporaryDirectory(prefix="dataset-showcase-") as temporary:
        working = Path(temporary)
        for name, expected_hash in EXPECTED_DIGESTS.items():
            archive = archives / f"{name}.zip"
            observed = hashlib.sha256(archive.read_bytes()).hexdigest()
            if observed != expected_hash:
                raise ValueError(f"Unexpected archive checksum: {name}; verify the download first")
            with ZipFile(archive) as bundle:
                for member in bundle.infolist():
                    # Only the original JPEGs needed by this audit are extracted.
                    path = Path(member.filename.replace("\\", "/"))
                    if path.suffix.lower() != ".jpg":
                        continue
                    if path.is_absolute() or ".." in path.parts or path.parts[0] != name:
                        raise ValueError("Unsafe image path in dataset archive")
                    destination = working / path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(bundle.read(member))
            root = working / name
            config = working / f"{name}.yaml"
            train = "images/train2017" if name == "coco128" else "images/train"
            val = train if name == "coco128" else "images/val"
            config.write_text(
                f"path: {json.dumps(root.as_posix())}\ntrain: {train}\nval: {val}\n",
                encoding="utf-8",
            )
            result = audit(config)
            expected_groups = 128 if name == "coco128" else 0
            if result["summary"]["confirmed_exact_groups"] != expected_groups:
                raise ValueError(f"Unexpected audit result for {name}")
            if name == "coco128":
                note = (
                    "COCO128 intentionally uses the same 128 images for Train and Validation. "
                    "This is a documented smoke-test configuration, "
                    "not an accidental dataset defect."
                )
            else:
                note = (
                    "The official COCO8 archive has four Train and four Validation images. "
                    "No exact cross-split image overlap was found; "
                    "source provenance remains unverified."
                )
            public = public_report(result, root, config, name, output, note)
            items = []
            if name == "coco128":
                for finding in result["findings"]:
                    member = finding["members"][0]
                    path = root / member["path"]
                    items.append(
                        {
                            "filename": path.name,
                            "path": member["path"],
                            "hash": finding["group_id"],
                            "splits": finding["splits"],
                            "image": thumbnail(path),
                        }
                    )
            else:
                for split in ("train", "val"):
                    for path in sorted((root / "images" / split).glob("*.jpg")):
                        items.append(
                            {
                                "filename": path.name,
                                "path": path.relative_to(root).as_posix(),
                                "hash": hashlib.sha256(path.read_bytes()).hexdigest(),
                                "splits": [split],
                                "image": thumbnail(path),
                            }
                        )
            items.sort(key=lambda item: item["filename"])
            data["datasets"][name] = {
                "summary": public["summary"],
                "checks": public["checks"],
                "status": public["status"],
                "items": items,
                "note": note,
                "archive_sha256": observed,
                "archive_url": f"https://github.com/ultralytics/assets/releases/download/v0.0.0/{name}.zip",
            }
            if name == "coco128":
                original = root / "images/train2017/000000000025.jpg"
                check_root = working / "filename-check"
                for relative in ("images/train/scene_014.jpg", "images/val/capture_928.jpg"):
                    target = check_root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(original.read_bytes())
                check_config = working / "filename-check.yaml"
                check_config.write_text(
                    f"path: {json.dumps(check_root.as_posix())}\n"
                    "train: images/train\nval: images/val\n",
                    encoding="utf-8",
                )
                check_result = audit(check_config)
                if check_result["summary"]["confirmed_exact_groups"] != 1:
                    raise ValueError("Different-filename check failed")
                finding = check_result["findings"][0]
                if finding["evidence"] != "confirmed_bytes":
                    raise ValueError("Different-filename check did not establish byte overlap")
                check_note = (
                    "Controlled filename-independence check: the original COCO128 image "
                    "000000000025.jpg was intentionally stored under two different filenames. "
                    "These are test copies, not the official COCO128 split configuration. "
                    "The original dataset was not modified."
                )
                public_report(
                    check_result, check_root, check_config, "filename-check", output, check_note
                )
                data["filename_check"] = {
                    "source_filename": original.name,
                    "source_path": original.relative_to(root).as_posix(),
                    "image": thumbnail(original),
                    "hash": finding["group_id"],
                    "members": finding["members"],
                    "status": check_result["status"],
                    "groups": check_result["summary"]["confirmed_exact_groups"],
                    "evidence": finding["evidence"],
                    "note": check_note,
                }
        data["similarity_examples"] = build_similarity(working, archives, output)
    template = REPOSITORY_ROOT / "showcase"
    for filename in ("index.html", "styles.css", "app.js", "mark.svg"):
        shutil.copyfile(template / filename, output / filename)
    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
    (output / "evidence.js").write_text(
        "window.SHOWCASE_EVIDENCE=" + payload + ";\n", encoding="utf-8"
    )
    write_credits(output, data)
    return {
        "output": str(output.resolve()),
        "datasets": {key: len(value["items"]) for key, value in data["datasets"].items()},
    }


def write_credits(output: Path, data: dict) -> None:
    """Keep original image IDs and source references with the public presentation."""
    image_names = sorted(
        {item["filename"] for dataset in data["datasets"].values() for item in dataset["items"]}
    )
    coco_links = "".join(
        f'<li><a href="https://cocodataset.org/#explore?id={int(Path(name).stem)}">'
        f"{html.escape(name)} — COCO source record</a></li>"
        for name in image_names
    )
    originals = {
        member["path"]: member
        for example in data["similarity_examples"]
        for member in example["members"]
    }
    benchmark_links = "".join(
        f'<li><a href="{html.escape(item["source_url"], quote=True)}">'
        f"{html.escape(path)}</a><br><code>{item['hash']}</code></li>"
        for path, item in sorted(originals.items())
    )
    content = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sources and image credits · Dataset Overlap Detector</title>
<style>body{{font:16px/1.7 system-ui,sans-serif;background:#f7f8f3;color:#193e2e;max-width:950px;
margin:40px auto;padding:0 24px}}a{{color:#245f46}}code{{overflow-wrap:anywhere;font-size:12px}}
li{{margin:12px 0}}.sources{{columns:3;column-gap:24px;font-size:13px}}
@media(max-width:700px){{.sources{{columns:1}}}}</style></head><body>
<a href="./">← Back to the showcase</a><h1>Sources and image credits</h1>
<p>Project code and original presentation are MIT licensed. Dataset images retain their
own original terms and are not relicensed under MIT.</p>
<h2>COCO images and original photographers</h2>
<p>These images come from the official Ultralytics COCO8/COCO128 archives. COCO images
originate from Flickr; individual image terms apply separately from annotation terms.
Credit belongs to the original photographers and COCO dataset team (Lin et al., ECCV 2014).
Original numeric IDs are preserved below.
Follow their source records to inspect image provenance.</p>
<p><a href="https://cocodataset.org/#termsofuse">COCO terms of use</a> ·
<a href="https://docs.ultralytics.com/datasets/detect/coco128/">COCO128 documentation</a> ·
<a href="https://docs.ultralytics.com/datasets/detect/coco8/">COCO8 documentation</a></p>
<details><summary>{len(image_names)} original COCO image references</summary>
<ul class="sources">{coco_links}</ul></details>
<h2>UBC and Leuven benchmark sequences</h2>
<p>Source: the Oxford affine-region evaluation benchmark, obtained from OpenCV's
official test-data repository. Original filenames and PNG bytes are retained.
Credits include the benchmark's contributing research groups and publications:
Mikolajczyk et al., IJCV 2005; Mikolajczyk and Schmid, PAMI 2005.</p>
<p><a href="https://www.robots.ox.ac.uk/~vgg/research/affine/">Original benchmark</a> ·
<a href="https://github.com/opencv/opencv_extra">OpenCV test-data repository</a></p>
<ul>{benchmark_links}</ul>
<h2>Example setup and evidence boundaries</h2>
<p>COCO128 reuse is documented and intentional. COCO8 has separate 4/4 image splits.
The renamed-image check is a controlled test. Benchmark Train/Validation assignments
are illustrative; they are not official splits or proof of benchmark leakage.
Video and recording-session histories remain unverified. Similarity percentages
are appearance scores, not leakage probabilities.</p>
<p><a href="https://github.com/asadozzaman/Dataset-Train-Test-Overlap-Detector/blob/main/THIRD_PARTY_NOTICES.md"
>Full third-party notices</a></p>
</body></html>"""
    (output / "credits.html").write_text(content, encoding="utf-8")


def build_similarity(working: Path, archives: Path, output: Path) -> list[dict]:
    """Audit intact benchmark files using disclosed, illustrative memberships."""
    manifest = json.loads(
        (REPOSITORY_ROOT / "examples/similarity_sources.json").read_text(encoding="utf-8")
    )
    examples = []
    for sequence in ("ubc", "leuven"):
        items = [item for item in manifest["files"] if item["sequence"] == sequence]
        root = working / f"similarity-{sequence}"
        root.mkdir()
        for item in items:
            source = archives / f"opencv-{sequence}" / item["filename"]
            content = source.read_bytes()
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ValueError(f"Unexpected benchmark checksum: {sequence}/{item['filename']}")
            (root / item["filename"]).write_bytes(content)
        (root / "train.txt").write_text("img1.png\n", encoding="utf-8")
        (root / "val.txt").write_text(
            "\n".join(item["filename"] for item in items if item["filename"] != "img1.png") + "\n",
            encoding="utf-8",
        )
        config = root / "data.yaml"
        config.write_text("train: train.txt\nval: val.txt\n", encoding="utf-8")
        result = audit(config, near_duplicates=True)
        if result["summary"]["confirmed_exact_groups"] != 0:
            raise ValueError("Benchmark images unexpectedly byte-identical")
        if result["summary"]["near_duplicate_candidates"] != len(items) - 1:
            raise ValueError("Expected benchmark similarity candidates were not found")
        note = (
            f"Original {sequence.upper()} benchmark images from OpenCV's official repository. "
            "This project did not edit or rename them. Train/Validation memberships were "
            "assigned only to exercise the detector; they are not official benchmark splits "
            "or evidence of leakage in the benchmark. Video/session origin is not verified."
        )
        name = f"similarity-{sequence}"
        public_report(result, root, config, name, output, note)
        by_filename = {item["filename"]: item for item in items}
        for finding in result["findings"]:
            members = []
            for member in finding["members"]:
                item = by_filename[member["path"]]
                members.append(
                    {
                        **member,
                        "filename": item["filename"],
                        "path": f"{sequence}/{item['filename']}",
                        "hash": item["sha256"],
                        "source_url": item["url"],
                        "image": "data:image/png;base64,"
                        + base64.b64encode((root / item["filename"]).read_bytes()).decode("ascii"),
                    }
                )
            examples.append(
                {
                    "id": f"{sequence}-{members[1]['filename'].split('.')[0]}",
                    "sequence": sequence,
                    "members": members,
                    "similarity": finding["similarity"],
                    "status": finding["status"],
                    "note": note,
                    "report": f"reports/{name}.html",
                    "json": f"reports/{name}.json",
                }
            )
    return examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/showcase"))
    parser.add_argument("--archives", type=Path, default=Path("data/public"))
    parser.add_argument("--github-url", help="Optional existing repository URL")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output, args.archives, args.github_url), indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Showcase build failed: {exc}\n")


if __name__ == "__main__":
    main()
