# CLI and report contract

Version 0.2, implemented by `videosplitguard audit`. `scan` is a compatibility alias.

```text
videosplitguard audit DATASET.yaml --output NEW_DIRECTORY
  [--root ROOT] [--provenance SOURCE.csv]
  [--near-duplicates] [--near-threshold 0..64]
  [--recommend-splits] [--fail-on confirmed|any|none]
```

`--near-threshold` requires `--near-duplicates`; default Hamming distance is 6.
Pillow is installed for image previews and is also used by `--near-duplicates`.
Install the `similarity` extra for NumPy when requesting this check. Each candidate
has a `similarity` object containing the raw SSIM, structural similarity percentage,
dHash bit distance and agreement percentage, method ID, low-information flag and
method note. SSIM percentages are `100 * max(0, raw_ssim)`; dHash agreement is
`100 * (64 - distance) / 64`. Neither measures the fraction of pixels that overlap,
nor the probability of leakage. The candidate status stays NOT VERIFIED regardless
of a high score. The optional-check block records structural comparisons and their
500-pair cap. Exact findings are not repeated as near-duplicate candidates.
The scan never downloads data or executes YAML directives. Return codes are 0 for a
completed scan satisfying the exit policy, 1 for a completed scan violating it, and 2
for invalid input or an operational error. Default `confirmed` fails on byte, video,
or session findings backed by verified metadata. `any` includes candidates. `none`
never turns an input error into success.

The report's overall status has a different purpose:

- **FAIL**: any confirmed cross-split finding.
- **NOT VERIFIED**: no confirmed finding, but incomplete/unreviewed source coverage or
  an inconclusive requested similarity check.
- **PASS**: no confirmed finding, complete reviewed video and session coverage, and no
  unverified result from an optional check. This relies on the user's source records.

`report.json` is deterministic for identical inputs at the same paths: there is no
scan timestamp. Key order and finding order are stable. The offline HTML is a readable
rendering of the same findings, with all user-controlled strings escaped and no external
assets or scripts. Artifacts are written in a private sibling staging directory first,
then published to an exclusively created output directory, with JSON moved last. A
write or move failure returns 2 and rolls back artifacts created by this call; a
concurrently created destination is preserved. Abrupt process termination or an OS
error during rollback may still leave incomplete files; this is not a crash-atomic
directory transaction.

HTML findings include side-by-side, split-labeled image cards and links to original
files. Previews are embedded JPEG data URLs; JSON contains references and evidence,
without image data. Moving the HTML preserves previews, while original-image links
require access to the original local dataset. Preview decoding failures are displayed
as placeholders and do not alter detector findings or check statuses.

Preview limits: 384×256 pixels; at most 8 memberships per group sampled across splits,
200 unique source images, 300 displayed thumbnails, 8 MiB of encoded image content,
64 MiB per source file, and 16 megapixels per source image. All member paths and
metadata remain in the report. The HTML explicitly discloses omitted/unavailable previews.

## JSON structure

| Field | Contents |
|---|---|
| `schema_version` | `0.2` |
| `tool` | Product name and package version |
| `status` | Overall PASS, FAIL, or NOT VERIFIED |
| `dataset` | Resolved YAML, root, and optional provenance CSV paths |
| `checks` | PASS/FAIL/NOT VERIFIED for exact, video, and session |
| `summary` | Split memberships, unique paths, finding counts, affected membership unions |
| `provenance` | Verified, unverified, and missing memberships separately for video and session |
| `optional_checks` | Similarity status, threshold, bounds, comparison count, truncation reason |
| `split_recommendations` | Null unless requested; otherwise target/proposed counts and all proposed rows |
| `findings[]` | Kind, status, evidence, group ID, split list, image paths and references |
| `recommendations[]` | Actions matched to observed results and coverage |
| `warnings[]`, `limitations[]` | Input caveats and boundaries of the conclusions |

Finding evidence values: `confirmed_shared_path`, `confirmed_bytes`,
`verified_metadata`, `unverified_metadata`, and `perceptual_dhash`. A mixed group may
produce separate verified and candidate findings so an unverified member is never
upgraded by another row. Identical source IDs without reviewed references stay
unverified. Numeric filenames do not become video IDs.

Each exact finding also lists `shared_paths`: the physical paths assigned to multiple
splits inside that byte-equivalence group. This stays visible when the group also
contains renamed copies. `summary.shared_path_groups` counts affected hash groups;
`summary.shared_path_count` counts distinct shared image paths. A provenance CSV must
have all fields on every row; an explicitly blank value is allowed, a missing field is
an input error.

`split_recommendations.rows` is also exported to `suggested_splits.csv` with columns
`path,current_splits,proposed_split,component_id`. One row represents a unique image
path. `current_splits` is semicolon-separated if a file belongs to multiple splits.
The proposal joins all byte-identical paths and paths with reviewed video/session IDs;
unverified IDs do not constrain it. Approximate ratio targets derive from current
membership counts. `deviation_counts` gives proposed minus target counts; `empty_splits`
and `warnings` disclose unusable allocations. Proposal status is `REVIEW REQUIRED`
when a configured split is empty or the largest group exceeds every target size;
otherwise it is `PROPOSED`. It makes no class-balance promise and never writes dataset files.

Paths inside the dataset root use forward-slash relative spelling; external image
paths are absolute. Reports contain local paths and references, so review before
sharing. A completed scan with NOT VERIFIED status is not a leakage-free certificate.
