"""Small, defined image-comparison metrics. Scores are never provenance proof."""

from pathlib import Path

from videosplitguard.models import DatasetError

SIZE = 128
WINDOW = 7
MAX_PIXELS = 16_000_000
METHOD = "ssim_grayscale_128_uniform7"


def require_numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise DatasetError(
            "Similarity scoring requires NumPy; install videosplitguard[similarity]"
        ) from exc
    return np


def grayscale(path: Path):
    """EXIF orientation, grayscale, then fixed 128x128 LANCZOS resampling."""
    from PIL import Image, ImageOps

    np = require_numpy()
    try:
        with Image.open(path) as source:
            if source.width * source.height > MAX_PIXELS:
                raise DatasetError(f"Similarity image exceeds {MAX_PIXELS} pixels: {path}")
            image = ImageOps.exif_transpose(source).convert("L")
            image = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
            return np.asarray(image, dtype=np.uint8).copy()
    except Image.DecompressionBombError as exc:
        raise DatasetError(f"Image exceeds Pillow's safe decoding limit: {path}") from exc


def structural_similarity(left, right) -> float:
    """Mean local SSIM: valid 7x7 windows, sample covariance, range 255.

    This uniform-window variant uses K1=.01 and K2=.03. Integral images
    calculate local moments without SciPy. No alignment or color analysis.
    """
    np = require_numpy()
    x, y = np.asarray(left, dtype=np.float64), np.asarray(right, dtype=np.float64)
    if x.shape != (SIZE, SIZE) or y.shape != x.shape:
        raise ValueError("SSIM inputs must both be normalized 128x128 grayscale arrays")

    def mean(values):
        integral = np.pad(values, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        return (
            integral[WINDOW:, WINDOW:]
            - integral[:-WINDOW, WINDOW:]
            - integral[WINDOW:, :-WINDOW]
            + integral[:-WINDOW, :-WINDOW]
        ) / (WINDOW * WINDOW)

    ux, uy = mean(x), mean(y)
    correction = WINDOW * WINDOW / (WINDOW * WINDOW - 1)
    vx = np.maximum(0, correction * (mean(x * x) - ux * ux))
    vy = np.maximum(0, correction * (mean(y * y) - uy * uy))
    covariance = correction * (mean(x * y) - ux * uy)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    values = ((2 * ux * uy + c1) * (2 * covariance + c2)) / (
        (ux * ux + uy * uy + c1) * (vx + vy + c2)
    )
    return float(np.clip(values.mean(), -1.0, 1.0))


def score_pair(left, right, distance: int) -> dict:
    np = require_numpy()
    score = structural_similarity(left, right)
    return {
        "method": METHOD,
        "ssim": round(score, 6),
        "structural_similarity_percent": round(max(0, score) * 100, 2),
        "dhash_distance": distance,
        "dhash_bits": 64,
        "hash_agreement_percent": round((64 - distance) / 64 * 100, 2),
        "low_information": bool(min(np.std(left), np.std(right)) < 5),
        "note": (
            "SSIM x 100, clipped at zero; appearance score, not leakage probability. "
            "EXIF-oriented grayscale images resized to 128x128; uniform 7x7 windows, "
            "sample covariance, data range 255. Color and geometric alignment are not checked."
        ),
    }
