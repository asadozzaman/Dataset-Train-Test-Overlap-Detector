# Architecture

The application uses one Python package and one synchronous CPU process.
It does not require a database or a background service.

```text
YOLO data.yaml ──> dataset.py ──> Sample(path, split)
CSV metadata ────> provenance.py ──> ProvenanceRecord(path, IDs, evidence, reference)
                                    │
                 ┌──────────────────┼───────────────────────┐
                 │                  │                       │
       detectors/exact.py  detectors/groups.py  detectors/near.py (opt-in)
                 └──────────────────┼───────────────────────┘
                                    v
                            audit.py (status + findings)
                                    │
                    ┌───────────────┴──────────────┐
                    v                              v
               report.py                   recommend.py (opt-in)
            JSON + offline HTML             suggested_splits.csv
```

`cli.py` implements `videosplitguard audit` and exit policy; `__main__.py` supports
`python -m videosplitguard`. `models.py` holds small immutable contracts. Tests are
offline by default; `scripts/verify_public_datasets.py` performs opt-in official-data
verification. `.github/workflows/tests.yml` specifies Windows/Ubuntu and Python
3.10/3.13 checks when CI is connected to a remote repository.

The runtime requires Python 3.10+, PyYAML 6.x, and Pillow for report previews and dHash;
NumPy is an optional similarity dependency. pytest, Ruff, and build are development
dependencies. FiftyOne, Datumaro, Ultralytics,
Torch, OpenCV, pandas, models, and GPUs are not runtime requirements.

## Data and evidence model

A sample is a resolved image path and split membership. The same resolved path in two
splits is a leak even if there is one physical file. Repeated references within one
split are collapsed with a warning. Streaming SHA-256 hashes each unique path once;
groups crossing splits become exact findings. A shared path is labeled separately
from distinct paths with identical bytes. File size and modification time are checked
before and after hashing to catch changes during the read.

CSV paths join to dataset-root-relative paths, never bare filenames. IDs are treated
as global within the dataset. A reviewed source row needs a nonempty `source_ref`.
Verified video/session matches across splits are confirmed *metadata assertions*;
other matches are candidates. Missing rows or IDs remain unknown. Full reviewed
coverage with no findings permits PASS, with an explicit reminder that references
are not independently authenticated. Conflicting video-to-session mappings fail.

Video and session groups use the same detector with independent IDs. Confirmed and
candidate members stay separate. Findings are groups rather than all possible pairs.
Summary counts use membership unions to avoid adding the same image twice when video
and session detectors both flag it.

Optional dHash decodes on the CPU, applies EXIF orientation, converts to grayscale,
and compares 64-bit hashes. It caps input at 2,000 images and 16 million pixels per
image, with at most 500 candidate groups. At most 1,999,000 path pairs are compared;
the cap or truncated output is disclosed as NOT VERIFIED. A dHash match is a visual
review candidate, not source proof. The method will miss crops and some transforms,
and can match unrelated low-detail frames. Each retained candidate also receives
local structural similarity (SSIM) using NumPy integral images: EXIF-oriented
grayscale inputs resized to 128x128, valid uniform 7x7 windows, sample covariance,
K1=.01, K2=.03, and data range 255. At most 500 SSIM comparisons are performed.
Normalized uint8 images are cached only as needed (up to 32.8 MB for 2,000 images).
Negative raw SSIM values remain in JSON; display percentages clip them to zero.
The scorer does not align images or compare color. Scores are appearance metrics,
never leakage probabilities. A low-information flag warns about nearly flat images.

The optional split planner makes connected components of byte-identical images and
reviewed video/session IDs, including groups currently confined to one split. It
assigns whole components using deterministic size-first, minimum-ratio-deviation
scoring with a preference for existing membership on ties. It writes a proposal only.
Large groups can make ratios unattainable; class balance and unreviewed source IDs are
not constraints. Target differences and empty splits are shown explicitly; an
infeasible allocation is labeled REVIEW REQUIRED. No image, label, or YAML file is moved or rewritten.

## Operational boundaries

The package does not train models or operate a server. Core hashing is linear in file
bytes and stores one hash per image. Reports are deterministic for unchanged inputs at
the same paths, use inline CSS, and contain no remote assets or JavaScript. Source
files should remain unchanged during an audit; the per-file stat check detects
mutation during hashing but cannot prove the entire tree stayed frozen. A report-write
error returns code 2. Reports are staged before exclusive creation of their final
directory and JSON is published last. Ordinary publication failures roll back owned
files; abrupt termination or rollback errors may still leave incomplete output.
Results are local and may contain sensitive path or source-reference text; review before sharing.

`previews.py` creates bounded JPEG thumbnails with source metadata removed. The HTML
renderer groups image cards by finding, labels each split, and includes original-file
links. JPEG data URLs keep the report self-contained. Selection alternates splits so
a large training group cannot hide the validation/test example. Thumbnail limits do
not remove member references or affect leakage classifications. The preview layer
handles missing/corrupt images with placeholders; JSON stays free of embedded pixels.
