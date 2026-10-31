# Phase 1 research evidence

Verification date: 2026-10-31. Engine: `videosplitguard 0.2.0a4`.
Initial checkout: `19e7076ab83a400fe4252aff6f6eca55d355acce`.

## Fresh verification

`python scripts/verify_public_datasets.py --output reports/phase1-20261031/public`
re-extracted the cached official archives and ran the real auditor. COCO128:
128 unique files, 128 Train + 128 Validation memberships, 128 exact groups.
COCO8: 8 unique files, 4 Train + 4 Validation, zero exact groups. Missing source
histories remain NOT VERIFIED. Controlled copy/provenance tests are separate.

`python scripts/fetch_similarity_examples.py` checked all six original PNG digests
against `examples/similarity_sources.json`, pinned to OpenCV commit
`ebf9366b3845efe1e54bf2440cf238fd68905bab`.
The showcase build reruns dHash/SSIM through the actual audit engine with a dHash
distance threshold of 6. Benchmark memberships are illustrative, not official splits.

| Comparison | SSIM × 100 | Fresh dHash distance / 64 |
|---|---:|---|
| UBC img1 / img4 | 97.46% | 0 |
| UBC img1 / img5 | 92.61% | 1 |
| UBC img1 / img6 | 86.11% | 3 |
| Leuven img1 / img2 | 72.01% | 0 |

All values were reproduced by the fresh showcase build. The four downloadable YAML
configurations were then copied into a separate directory, populated with original
inputs, and executed through `python -m videosplitguard audit`. All summaries and
similarity values matched the published local records. COCO128 exited 1 as expected;
COCO8, UBC and Leuven exited 0 while source histories remained NOT VERIFIED.
Verification record: `reports/phase1-20261031/reproduction/verification.json`.

SSIM uses oriented grayscale 128×128 images and uniform 7×7 windows. dHash uses
64 bits. Scores describe appearance, never leakage probabilities. See
`src/videosplitguard/similarity.py` and `docs/RESEARCH.md` for limitations.

## Original sources and terms

- [Ultralytics COCO128](https://docs.ultralytics.com/datasets/detect/coco128/)
  explicitly documents intentional reuse of the same images for both splits.
- [Ultralytics COCO8](https://docs.ultralytics.com/datasets/detect/coco8/)
  documents the 4/4 configuration. Archive digests are pinned in the build script.
- [Oxford affine benchmark](https://www.robots.ox.ac.uk/~vgg/research/affine/index.html)
  identifies illumination and JPEG-compression sequences and contributing groups.
- Original OpenCV URLs and all six digests: `examples/similarity_sources.json`.
- [COCO terms](https://cocodataset.org/#termsofuse): image terms differ from
  annotation terms. Original numeric IDs and source-record links are retained.

**Publication remains pending source-rights verification.** Public accessibility
and an OpenCV source URL do not establish image redistribution permission. The
reviewed benchmark landing page and pinned OpenCV README do not supply explicit
terms for these sequences. COCO photographer/license records are also not bundled
in the current archives. Obtain and record applicable permissions and attribution
before publishing the generated image-bearing site. No license is inferred from
OpenCV's software license. This is separate from the verified audit measurements.

## Reproduction and inspectable outputs

See `docs/DEPLOYMENT.md` for setup. Build into a new directory:

```text
python scripts/fetch_similarity_examples.py
python scripts/build_showcase.py --output reports/phase1-20261031/site --github-url https://github.com/asadozzaman/Dataset-Train-Test-Overlap-Detector
```

The generated experiment manifest records configuration, input checksums, engine
fingerprint, runtime versions, measurements, caveats and report links. Source data
and generated reports remain outside Git. No private material is needed.


## Source-link publication — 2026-10-31

The owner selected publication of verified results and original-source links without
hosting the photos. `scripts/export_source_links.py` exports that version, strips
embedded report previews, omits dataset assets, and retains all scientific results.
The artifact records `source_links_only`; redistribution rights remain unverified.
The full local visual showcase is retained. No new permission claim is made.
