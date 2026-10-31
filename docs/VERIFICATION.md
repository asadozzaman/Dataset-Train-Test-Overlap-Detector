# Verification ledger

The engine/platform baseline below covers **0.2.0a2**, tested on **2026-10-20**.
Visual report verification for **0.2.0a3** is recorded in the final section.
All real datasets came from official
Ultralytics release URLs via `scripts/verify_public_datasets.py`; source ZIP files,
extractions and outputs are Git-ignored.

## Public datasets

| Case | Train / val | Exact groups | Video/session | Outcome |
|---|---:|---:|---|---|
| COCO8 original | 4 / 4 | 0 | NOT VERIFIED | Expected baseline |
| COCO128 original | 128 / 128 | 128 shared-path groups | NOT VERIFIED | Expected intentional overlap |
| COCO8 with one copied training image in validation | 4 / 5 | 1 | NOT VERIFIED | Injected overlap detected |
| COCO8 with test-only synthetic CSV | 4 / 4 | 0 | 1 video and 1 session group | Synthetic metadata engine verified |

COCO8/COCO128 do not supply verified video histories. The CSV for the last row is
named `synthetic-provenance.csv`, uses `SYNTHETIC-*` IDs and a
`test-only-synthetic-manifest` reference, and is never described as real COCO history.
Numeric COCO image names were not interpreted as video IDs. COCO128's shared
Train/Validation paths are intentional in [Ultralytics' documentation](https://docs.ultralytics.com/datasets/detect/coco128/).

Observed archive SHA-256 digests:

```text
coco8.zip    54c67fe9ef88313e021ec0e92b73c200167bb0a86633e8df8658d832cca828c9
coco128.zip  61e5e3028863d8ffc3b81d6a514603954889f0edd5e4b44c4ce60b2da99aeb8e
```

These identify downloaded bytes; they are not independently authenticated upstream
checksums. Current real-data ledgers and reports are under
`reports/verification-20261020/windows-public/` and
`reports/verification-20261020/linux310/public/`. The current CLI demonstration report
and proposed split CSV are under `reports/verification-20261020/windows-demo/`.

## Automated and manual checks

| Platform | Python | Installation | Outcome |
|---|---|---|---|
| Windows | 3.10.10 | Editable package in `.venv` | 56 passed |
| Windows | 3.13.7 | Built wheel in `.venv-313`, tested outside checkout | 56 passed |
| Linux container | 3.10.22 | Built wheel, checkout mounted read-only | 56 passed |
| Linux container | 3.13.16 | Built wheel, checkout mounted read-only | 56 passed |

Saved JUnit records: `reports/verification-20261020/windows313.xml`,
`linux310/pytest.xml`, and `linux313/pytest.xml`. Each has 56 tests, zero failures,
zero errors and zero skips. Windows 3.10 results were captured in the command output.

- [x] CSV evidence separation, image decoding, bounded similarity, group proposals,
      source immutability, failed-publication rollback and concurrent output protection.
- [x] A shared path remains visible when its hash group also contains renamed copies.
- [x] Missing CSV fields and Pillow decoding limits return readable input errors.
- [x] Infeasible proposals disclose empty splits and target differences, with a
      REVIEW REQUIRED status in HTML and the CLI.
- [x] Ruff lint and formatting passed.
- [x] Official COCO8, COCO128, injected copy, and synthetic provenance script passed.
- [x] Actual installed CLI `videosplitguard audit` ran against both public datasets;
      COCO128 exited 1, COCO8 without metadata exited 0 with NOT VERIFIED status,
      synthetic video/session CSV exited 1.
- [x] Updated standalone HTML opened in headless Chrome at 1280×2600 and was visually
      reviewed, including the proposed/target/difference table.
- [x] HTML strings are escaped by test; identical JSON/HTML for identical inputs are
      asserted; proposed CSV and dataset immutability are tested.
- [x] Official COCO verification also passed on Linux Python 3.10: zero exact groups
      on COCO8, 128 on COCO128, one injected-copy group and the expected synthetic groups.
- [x] The 0.2.0a2 wheel built successfully and was installed for the platform checks.
- [ ] Hosted GitHub Actions results are separate from the local Windows and Linux
      container verification recorded here.

## Linux reproducibility

Docker Desktop was started locally for these CPU-only tests. Containers used official
Python images and installed the built wheel with the `similarity` extra and pytest.
The checkout was mounted read-only at `/workspace`, results were written through a
separate `/results` mount, and the containers were removed after completion.

Observed image digests:

```text
python:3.10-slim  sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d
python:3.13-slim  sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
```

Inside each container, tests ran from `/tmp` with:

```bash
python -m pytest /workspace/tests -q -p no:cacheprovider --junitxml=/results/pytest.xml
```

Linux report YAML files contain container paths; use the `windows-public` configs
when rerunning the demo from Windows.

Run tests with `.\.venv\Scripts\python.exe -m pytest -q` on Windows. To rerun public
verification, choose a new `--output` directory. All report output directories are
write-once by design.

## Visual reports (0.2.0a3)

Verified on 2026-10-30 using the existing official dataset archives. A separate
COCO8 extraction was used for the copied-image demonstration, leaving the original
archives and baseline dataset untouched.

All 63 tests passed in each of the four supported platform/version combinations:
Windows Python 3.10/3.13 and Linux container Python 3.10/3.13. The Windows 3.13 and
both Linux runs used the built 0.2.0a3 wheel. JUnit results are saved under
`reports/image-evidence/windows313-tests.xml`, `linux310/pytest.xml`, and
`linux313/pytest.xml`. Linux Python 3.10 also completed the official COCO verification
script, with the expected baseline, intentional overlap, copied-image, and synthetic
provenance outcomes.

| Report | Findings | Embedded previews |
|---|---:|---:|
| COCO8 with an intentionally copied training image in validation | 1 exact group | 2 |
| Official COCO128 shared Train/Validation paths | 128 exact groups | 256 |
| COCO8 with clearly labeled synthetic video/session metadata | 1 video and 1 session group | 4 |

The reports are under `reports/image-evidence/`. Every image source in the HTML is
an embedded JPEG data URL; no remote image service or external asset folder is used.
Cards include split labels, member paths, metadata references when supplied, and
links to open the original local images. Moving the HTML preserves the thumbnails.

The visual-report suite checks thumbnail dimensions, deterministic output, embedded
data decoding, source-file immutability, selection across different splits, complete
member references, budget limits, and corrupt/missing-image placeholders. It also
checks that metadata groups are not described as visually identical images.

The copied-image report was rendered and visually reviewed in Chrome, including
the paired images, split labels, filenames and original-image links. Generated
reports contain dataset thumbnails and remain excluded from Git.

## Showcase

The local showcase is built by `scripts/build_showcase.py` using the pinned official
archives and the actual audit engine. It contains all 128 COCO128 overlap groups and
the 8 original COCO8 images, preserving original filenames, paths and SHA-256 digests.
COCO128 reuse is labeled intentional; COCO8's overall source status remains NOT VERIFIED.
Official dataset results retain original filenames. A separate controlled filename check intentionally stores one original photo under two names, runs the actual engine, and exposes its own HTML/JSON report. It is clearly labeled as a capability check. No synthetic provenance is presented as authentic history.

Eight DOM-based interaction checks pass for selection/search, dataset tabs, keyboard
interaction, image dialogs, commands/clipboard fallback, internal links, original
references and public report sanitization. The Python suite also passes all 63 tests.
Source-package validation confirms that showcase source is included while node_modules
and generated third-party image assets are excluded.

Browser automation was unavailable during this showcase task. DOM checks establish
interactive behavior but do not substitute for desktop/mobile visual layout review.

## Similarity scoring — version 0.2.0a4, October 30, 2026

The 68-test Python suite passed on Windows 3.10.10 and 3.13.7, and in official Linux
Python 3.10.22 and 3.13.16 containers. Installed-wheel runs include the similarity
extra. Ten showcase DOM checks passed, including selection of measured comparisons,
source links, original embedded PNG checksums, metric updates, modal inspection and
report availability. Ruff lint/format checks passed.

The SSIM implementation matched scikit-image 0.25.2 on five random pairs and one
real benchmark pair (absolute error below 1e-10). Tests also cover a separate direct
window calculation, identity, symmetry, negative-score display clipping, low-detail
false positives, optional-dependency errors, repeatability and the 500-comparison cap.
Scikit-image was a validation reference; it is not a package dependency.

Public verification reran successfully: COCO128 has 128 intentional exact-overlap
groups; COCO8 has zero, with source histories NOT VERIFIED. Synthetic source records
and an injected-copy regression remain explicitly test-only.

UBC original `img1.png` compared with `img4.png`, `img5.png`, and `img6.png` yielded
97.46%, 92.61%, and 86.11% SSIM respectively. Leuven `img1.png`/`img2.png` yielded
72.01% SSIM and 100% dHash agreement. These are appearance measures, not leakage
probabilities. All benchmark files have distinct SHA-256 hashes. Files came from the
pinned OpenCV commit in `examples/similarity_sources.json`; this project did not alter
them. Example split memberships are illustrative, never described as original splits.
Actual CLI output is under `reports/similarity-verification/ubc/`; public dataset
records are under `reports/similarity-verification/public-data/`. Generated public
showcase copies contain no machine paths and keep missing provenance unverified.

Full desktop/mobile browser-layout review remains incomplete because local browser
control was disabled. DOM checks do not establish visual layout quality.


## Phase 1 showcase revision — 2026-10-31

The Python engine is unchanged. Fresh official-archive verification reproduced
COCO128's 128 intentional groups and COCO8's zero exact groups (128/128 and 4/4
memberships respectively). All six benchmark PNGs matched pinned digests. Fresh
UBC SSIM results are 97.46%, 92.61%, 86.11%; Leuven is 72.01% with dHash distance 0.
The downloadable experiment YAML files were independently populated with original
inputs and run through the actual CLI: all four report summaries and similarity
measurements matched. COCO128 exit 1 is expected; the other examples exit 0 with
source histories NOT VERIFIED.

Executed from the repository, with Python 3.10.10 on Windows:

```powershell
.\.venv\Scripts\python.exe scripts/verify_public_datasets.py --output reports/phase1-20261031/public
.\.venv\Scripts\python.exe scripts/fetch_similarity_examples.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m build
```

Results: 68 Python tests passed; lint and formatting passed; wheel and source
archive built. No new Linux or Python 3.13 run is claimed for this website revision.

The static build was generated with `scripts/build_showcase.py --github-url
https://github.com/asadozzaman/Dataset-Train-Test-Overlap-Detector` into fresh
subdirectories of `reports/phase1-20261031/`. It contains 39 KB of evidence metadata
rather than embedded image payloads. Original benchmark PNG bytes are separate
assets, verified against their source SHA-256 values by the DOM suite.

With `SHOWCASE_OUTPUT` set to the absolute generated directory, executed from
`showcase/`: `npm test` (12 passed) and `npm run test:browser` (7 browser subchecks
plus their parent passed). Real installed Chrome loaded the site beneath the
actual `/Dataset-Train-Test-Overlap-Detector/` prefix. Widths 320, 390, 768, 1024,
1440 had no page-level horizontal overflow. axe WCAG 2 A/AA and 2.1 AA rules reported
zero violations on those layouts, COCO8, the image dialog and Leuven states.
Keyboard tab selection, search, dialog Escape/focus restoration, source assets,
report/configuration downloads, platform commands and local HTTP links passed.
This is automated accessibility coverage, not certification or screen-reader testing.

Generated desktop/mobile screenshots were visually inspected, including real
compression imagery after lazy images loaded. Screenshots and axe records are in
`reports/phase1-20261031/browser/`. An initially detected keyboard-focus issue in
scrollable command blocks was fixed before the passing run.

**Phase 1 release is not yet complete:** benchmark redistribution terms and
complete individual COCO attribution remain unresolved. See
[the evidence ledger](../RESEARCH_EVIDENCE.md). The Pages workflow stops before
artifact upload while `publication.rights_verified` is false; its Python guard was
executed against the generated manifest and correctly exited 1 with the recorded
publication reason. No deployment was
performed during this revision; hosted CI status remains separate from local QA.


### Visual comparison follow-up — 2026-10-31

`npm test`: 13 passed. `npm run test:browser`: 8 subchecks plus parent passed.
The new four-case explorer was checked against source evidence for filenames,
image references, hashes, report links and measured values. Real Chrome exercised
all four cases, keyboard navigation, technical disclosure and image enlargement;
axe A/AA checks found no violations in each case. Five viewport widths and the
full dataset explorer interactions passed. The browser test now waits for the
primary comparison image; the previous image-list wait targeted a section that
is intentionally collapsed. Screenshots are under `reports/phase1-20261031/browser/`.
Only the website and its checks changed; no audit engine or experiment changes.


### Source-link publication checks — 2026-10-31

The owner selected a public source-link edition without hosted photos. Fresh checks:
68 Python tests; 13 showcase DOM tests; two artifact/public-interaction tests;
Ruff lint and formatting passed. The public export rejects raster image files,
archives and embedded image data. Original source actions, all four comparison
cases, five widths and axe A/AA rules were checked in real Chrome and passed.
Image redistribution permission remains unresolved; the export records that fact.
The full local image-preview build is retained. Pages publishes only the checked
`showcase-public` export. Hosted run/deployment status is available in Actions.
