"""Bounded, metadata-free JPEG previews for portable HTML evidence reports."""

import base64
import io
import warnings
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

MAX_UNIQUE_IMAGES = 200
MAX_RENDERED_PREVIEWS = 300
MAX_EMBEDDED_BYTES = 8 * 1024 * 1024
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_SOURCE_PIXELS = 16_000_000
THUMBNAIL_SIZE = (384, 256)
MAX_MEMBERS_PER_GROUP = 8


@dataclass(frozen=True)
class Preview:
    data_url: str | None
    message: str | None


def _thumbnail(path: Path) -> Preview:
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            return Preview(None, "Image exceeds the 64 MiB preview input limit.")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as source:
                if source.width * source.height > MAX_SOURCE_PIXELS:
                    return Preview(None, "Image exceeds the 16 megapixel preview limit.")
                source.draft("RGB", (800, 800))
                oriented = ImageOps.exif_transpose(source)
                if oriented.mode in {"RGBA", "LA"} or "transparency" in oriented.info:
                    rgba = oriented.convert("RGBA")
                    image = Image.new("RGB", rgba.size, "white")
                    image.paste(rgba, mask=rgba.getchannel("A"))
                else:
                    image = oriented.convert("RGB")
                image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=78)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return Preview("data:image/jpeg;base64," + encoded, None)
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        return Preview(
            None, "Preview unavailable: image is missing, unreadable, or unsafe to decode."
        )


class ImagePreviews:
    """Cache decoding by resolved path and bound total embedded image content."""

    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[Path, Preview] = {}
        self.rendered = 0
        self.embedded_bytes = 0
        self.omitted = 0
        self.unavailable: set[Path] = set()

    def source_path(self, spelling: str) -> Path:
        return (self.root / spelling).resolve()

    def get(self, path: Path) -> Preview:
        if self.rendered >= MAX_RENDERED_PREVIEWS:
            self.omitted += 1
            return Preview(None, "Report preview limit reached; use the original image reference.")
        if path not in self.cache:
            if len(self.cache) >= MAX_UNIQUE_IMAGES:
                self.omitted += 1
                return Preview(None, "Unique-image preview limit reached.")
            self.cache[path] = _thumbnail(path)
        preview = self.cache[path]
        if preview.data_url is None:
            self.unavailable.add(path)
            return preview
        size = len(preview.data_url)
        if self.embedded_bytes + size > MAX_EMBEDDED_BYTES:
            self.omitted += 1
            return Preview(None, "Embedded-image budget reached; use the original image reference.")
        self.rendered += 1
        self.embedded_bytes += size
        return preview


def select_members(members: list[dict]) -> list[dict]:
    """Round-robin splits so a large training group cannot hide the other side."""
    by_split = {
        split: [m for m in members if m["split"] == split] for split in ("train", "val", "test")
    }
    selected = []
    for offset in range(MAX_MEMBERS_PER_GROUP):
        for group in by_split.values():
            if offset < len(group):
                selected.append(group[offset])
                if len(selected) == MAX_MEMBERS_PER_GROUP:
                    return selected
    return selected
