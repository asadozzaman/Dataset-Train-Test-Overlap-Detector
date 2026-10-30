# Project showcase

[Live showcase](https://asadozzaman.github.io/Dataset-Train-Test-Overlap-Detector/)
 · [Automatic GitHub Pages deployment](../docs/DEPLOYMENT.md)

A responsive, buildless presentation for Dataset-Train–Test Overlap Detector.
The interactive explorer uses fresh audit results from the official COCO128 and
COCO8 archives. Original image filenames, paths and SHA-256 digests are preserved.
The official dataset examples retain their authentic split configuration. A separate,
clearly labeled controlled filename check demonstrates that renaming an image does
not prevent detection. No synthetic source histories are presented as real provenance.

## Build locally

Install the Python project first. Cache the official datasets using the verification
script in the repository README, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install '.[similarity]'
.\.venv\Scripts\python.exe scripts\fetch_similarity_examples.py
.\.venv\Scripts\python.exe scripts\build_showcase.py --output reports\showcase
.\.venv\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1 --directory reports\showcase
```

Open `http://127.0.0.1:8765`. Use a new output directory on subsequent builds.
You can also open the built `index.html` directly; the site uses no network fonts,
image services or application backend. Clipboard support varies when using file URLs.

## Interaction checks

The showcase has a separate Node development test suite. After building it, run:

```powershell
cd showcase
npm ci
npm test
```

The tests use a DOM implementation, without driving a browser, to verify image
selection, original references, search, baseline switching, keyboard tabs, image
dialogs, platform commands, clipboard fallback, and internal links. This does not
verify browser layout; review desktop and mobile rendering separately when browser
automation is available. The static site does not require Node or jsdom at runtime.

If an existing GitHub repository is available, include
`--github-url https://github.com/OWNER/REPOSITORY` during the build. Otherwise, the
showcase accurately displays that repository publication is pending.

The builder verifies known archive checksums, runs the real audit engine, embeds
thumbnails, and includes portable HTML/JSON reports. Machine-specific paths and
original-file links are removed from the generated public copies. Source reports
and datasets are not modified. Nothing is uploaded by this command.

## Content boundaries

COCO128 intentionally assigns the same 128 files to Train and Validation. COCO8 is
the separate 4/4 image baseline. Neither provides reviewed video/session histories.
These limits are displayed alongside the findings, including the baseline's overall
NOT VERIFIED result. The software license does not relicense dataset images.

The different-filename section uses an original COCO128 photo stored under two
test filenames in a temporary dataset. The actual engine must detect one
`confirmed_bytes` group before the builder includes the section. Its separate
HTML/JSON report describes the controlled setup; the official dataset is not modified.

The COCO128 inspector shows each shared file once, together with its split memberships,
the dataset configuration explaining the finding, and the appropriate next action.
It is an evidence viewer. The distinct-filename check retains a two-file comparison
because the references differ. Dataset editing is performed separately from inspection.

Only the showcase source is intended for Git. Generated output contains third-party
image previews, remains under the ignored reports directory, and retains the dataset
source and terms links. Review applicable image terms before hosting or redistributing.
The generated `credits.html` preserves image IDs and original source links;
the repository's [third-party notices](../THIRD_PARTY_NOTICES.md) explain the source terms.

## Real similarity examples

The comparison section audits unchanged UBC compression and Leuven lighting images
from OpenCV's official test-data repository. `examples/similarity_sources.json` pins
each source URL, Git commit and SHA-256. Original PNG bytes are embedded directly in
the showcase, so preview re-encoding cannot obscure the comparison. Train/Validation
memberships in these example audits are illustrative assignments, not official
benchmark splits or proof of benchmark leakage. No source histories are invented.

Select a comparison to inspect both original references, SSIM and dHash scores,
different file hashes, source links and the actual audit report. A high appearance
score remains a candidate requiring review. A lighting example shows why these
percentages should never be presented as calibrated leakage probabilities.
