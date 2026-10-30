"""Opt-in real-data smoke verification; never runs in offline unit tests.

Download only the two fixed official archives. Record observed hashes, not a claim
of upstream checksum authentication. Source images stay in git-ignored data/.
"""

import argparse
import csv
import hashlib
import json
import shutil
import stat
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from videosplitguard.audit import audit
from videosplitguard.report import write_reports

BASE_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/"


def extract_checked(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        if sum(info.file_size for info in bundle.infolist()) > 100 * 1024 * 1024:
            raise ValueError("Archive exceeds 100 MiB extraction limit")
        for info in bundle.infolist():
            name = PurePosixPath(info.filename.replace("\\", "/"))
            mode = info.external_attr >> 16
            target = (destination / str(name)).resolve()
            if (
                name.is_absolute()
                or ".." in name.parts
                or ":" in str(name)
                or stat.S_ISLNK(mode)
                or not target.is_relative_to(destination.resolve())
            ):
                raise ValueError(f"Unsafe archive member: {info.filename}")
        bundle.extractall(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Allow official archive downloads")
    parser.add_argument("--data-dir", type=Path, default=Path("data/public"))
    parser.add_argument("--output", type=Path, default=Path("reports/public-verification"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new --output directory")
    args.data_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name, expected_files, expected_groups in [("coco8", 8, 0), ("coco128", 128, 128)]:
        archive = args.data_dir / f"{name}.zip"
        url = BASE_URL + archive.name
        if not archive.exists():
            if not args.download:
                parser.error(f"Missing {archive}; pass --download for opt-in network access")
            temporary = archive.with_suffix(".part")
            with (
                urllib.request.urlopen(url, timeout=60) as response,
                temporary.open("wb") as target,
            ):
                total = 0
                while block := response.read(1024 * 1024):
                    total += len(block)
                    if total > 30 * 1024 * 1024:
                        raise ValueError("Archive download exceeds 30 MiB")
                    target.write(block)
            temporary.replace(archive)
        # Unique run extraction prevents stale edits to a previous extraction affecting the audit.
        run_data = args.output / "inputs" / name
        run_data.mkdir(parents=True)
        extract_checked(archive, run_data)
        root = (run_data / name).resolve()
        config = run_data / "audit.yaml"
        train = "images/train" if name == "coco8" else "images/train2017"
        val = "images/val" if name == "coco8" else train
        config.write_text(
            f"path: {json.dumps(root.as_posix())}\ntrain: {train}\nval: {val}\n", encoding="utf-8"
        )
        report = audit(config)
        assert report["summary"]["unique_files"] == expected_files, report["summary"]
        assert report["summary"]["confirmed_exact_groups"] == expected_groups, report["summary"]
        assert report["provenance"]["source"] == "none"
        assert report["checks"]["source_video"] == "NOT VERIFIED"
        assert report["checks"]["recording_session"] == "NOT VERIFIED"
        write_reports(report, args.output / name)
        records.append(
            {
                "dataset": name,
                "url": url,
                "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "summary": report["summary"],
                "source_provenance": "NOT VERIFIED",
            }
        )
        if name == "coco8":
            # These IDs are deliberately invented test fixtures, not COCO origin claims.
            synthetic_csv = run_data / "synthetic-provenance.csv"
            train_image = sorted((root / "images/train").glob("*.jpg"))[0]
            val_image = sorted((root / "images/val").glob("*.jpg"))[0]
            with synthetic_csv.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["path", "video_id", "session_id", "evidence", "source_ref"])
                for image in (train_image, val_image):
                    writer.writerow(
                        [
                            image.relative_to(root).as_posix(),
                            "SYNTHETIC-video-1",
                            "SYNTHETIC-session-1",
                            "verified",
                            "test-only-synthetic-manifest",
                        ]
                    )
            provenance_report = audit(config, provenance_path=synthetic_csv)
            assert provenance_report["summary"]["confirmed_video_groups"] == 1
            assert provenance_report["summary"]["confirmed_session_groups"] == 1
            assert provenance_report["status"] == "FAIL"
            write_reports(provenance_report, args.output / "coco8-synthetic-provenance")
            records.append(
                {
                    "dataset": "coco8-synthetic-provenance",
                    "expected_video_groups": 1,
                    "expected_session_groups": 1,
                    "provenance": "SYNTHETIC TEST ONLY",
                    "passed": True,
                }
            )
            source = sorted((root / "images/train").glob("*.jpg"))[0]
            injected = root / "images/val/injected-copy.jpg"
            shutil.copyfile(source, injected)
            injected_report = audit(config)
            assert injected_report["summary"]["confirmed_exact_groups"] == 1
            write_reports(injected_report, args.output / "coco8-injected-copy")
            injected.unlink()
            records.append({"dataset": "coco8-injected-copy", "expected_groups": 1, "passed": True})
    result = {"verified_at": datetime.now(timezone.utc).isoformat(), "results": records}
    (args.output / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
