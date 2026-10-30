# Read an audit report

Open `report.html` for offline inspection, or use `report.json` for integration.
Bounded previews are embedded without external scripts, fonts or image services.
Original-file links refer to the local dataset and may stop resolving when moved.

## Read in this order

1. Overall FAIL, NOT VERIFIED, or PASS.
2. Per-check statuses: exact PASS does not verify source independence.
3. Reviewed, unreviewed and missing source coverage.
4. Optional-check completion and any skipped/truncated reason.
5. Findings, image references, cited source records, and recommendations.

FAIL is a successfully detected conflict. NOT VERIFIED needs more evidence or
inspection. Overall PASS relies on complete reviewed video/session assertions and
no unresolved optional check; source references are not independently authenticated.

## Exact images

`confirmed_shared_path` means the same resolved file belongs to different splits.
`confirmed_bytes` means distinct paths contain identical bytes. Renaming does not
hide byte overlap. Decoded pixel equality after re-encoding is outside the exact check.
Inspect members and shared paths, then keep the shared image in one evaluation
partition unless its reuse is intentional and documented, as with COCO128.

## Videos and sessions

Groups follow CSV IDs; their images need not look identical. Reviewed references
support confirmed metadata assertions. Unreviewed members remain separate candidates.
Review records before rebuilding source-group-aware splits.

## Similarity scores

The detector compares 64-bit dHash fingerprints across splits and excludes confirmed
exact pairs. Retained pairs include their file hashes and these metrics:

| Field | Meaning |
|---|---|
| `ssim` | Raw mean structural similarity, from -1 to 1 |
| `structural_similarity_percent` | `100 × max(0, ssim)`, rounded |
| `dhash_distance` | Differing bits out of 64 |
| `hash_agreement_percent` | Matching dHash-bit percentage |
| `low_information` | A normalized image has very little variation |
| `method`, `note` | Preprocessing and comparison settings |

SSIM uses EXIF orientation, grayscale conversion, 128×128 resizing, uniform 7×7
windows, sample covariance, K1=.01, K2=.03 and range 255. There is no geometric alignment.

**92.61% SSIM does not mean 92.61% leakage or confidence.** Lighting, compression,
crop, rotation, color and low detail affect scores; unrelated flat images can score
highly. Candidates remain NOT VERIFIED even at 100%. Inspect scene details and source
records; related captures or alternate versions should stay together when splitting.

## Proposed splits

`--recommend-splits` writes `suggested_splits.csv` with current memberships, proposed
assignments and connected components. It keeps exact-byte groups and reviewed source
IDs together. Unverified similarity candidates are not automatically treated as
proven source groups. No files move.

The plan approximates existing ratios. An empty split or oversized indivisible group
produces REVIEW REQUIRED. Labels, class balance and evaluation constraints need
separate review before applying any proposal.

## JSON map

| Field | Content |
|---|---|
| `schema_version`, `tool` | Contract and application versions |
| `status`, `checks` | Overall and per-check outcomes |
| `dataset` | Configuration, root and provenance input |
| `summary` | Membership, file, confirmed-group and candidate counts |
| `provenance` | Reviewed/unreviewed/missing coverage and evidence limitations |
| `optional_checks` | Settings, limits, comparisons and completion |
| `findings` | Evidence, paths/splits, optional hashes and scores |
| `split_recommendations` | Proposal summary, or null |
| `recommendations`, `warnings`, `limitations` | Next steps and boundaries |

A file shared by Train and Validation has two memberships. Groups, files and
memberships are different units. Affected-membership totals use unions across
detectors. Identical inputs at the same paths produce deterministic reports with
no scan timestamp.

[CLI exit policy](CLI.md#exit-codes) · [Detailed contract](CONTRACTS.md) · [Documentation home](README.md)
