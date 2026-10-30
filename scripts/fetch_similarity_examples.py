"""Fetch pinned, checksum-verified benchmark images from OpenCV's official repository."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

MANIFEST = Path(__file__).resolve().parents[1] / "examples" / "similarity_sources.json"
MAX_DOWNLOAD = 8 * 1024 * 1024


def fetch(folder: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for item in manifest["files"]:
        target = folder / f"opencv-{item['sequence']}" / item["filename"]
        if target.exists():
            content = target.read_bytes()
        else:
            with urlopen(item["url"], timeout=30) as response:
                content = response.read(MAX_DOWNLOAD + 1)
        if len(content) > MAX_DOWNLOAD:
            raise ValueError(f"Download exceeds the size limit: {item['filename']}")
        if hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise ValueError(f"Unexpected checksum: {item['sequence']}/{item['filename']}")
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        print(f"Verified {item['sequence']}/{item['filename']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/public"))
    args = parser.parse_args()
    try:
        fetch(args.output)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Example download failed: {exc}\n")
