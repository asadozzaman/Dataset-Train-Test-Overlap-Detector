# CLI reference

```text
videosplitguard audit DATASET.yaml --output NEW_DIRECTORY
  [--root ROOT] [--provenance SOURCE.csv]
  [--near-duplicates] [--near-threshold 0..64]
  [--recommend-splits] [--fail-on confirmed|any|none]
```

`scan` is a compatibility alias. `python -m videosplitguard` exposes the same CLI.
`videosplitguard --version` prints the installed version.

| Option | Default | Behavior |
|---|---|---|
| `DATASET.yaml` | Required | Local YOLO configuration |
| `--output` | Required | New HTML/JSON output directory |
| `--root` | YAML root | Override dataset root |
| `--provenance` | None | Source CSV with evidence and references |
| `--near-duplicates` | Off | Enable bounded dHash + SSIM; requires similarity extra |
| `--near-threshold` | 6 | Maximum differing bits out of 64; requires near-duplicate checking |
| `--recommend-splits` | Off | Write a proposed CSV without moving files |
| `--fail-on` | `confirmed` | Completed-audit exit policy |

The threshold is a **bit distance**, not a percentage. Lower is stricter; higher can
increase false positives. SSIM describes retained candidates and never automatically
confirms provenance.

## Examples

```bash
videosplitguard audit data/data.yaml --output reports/exact-check
videosplitguard audit data/data.yaml --provenance data/sources.csv --output reports/source-check
videosplitguard audit data/data.yaml --near-duplicates --near-threshold 6 --output reports/similarity-check
videosplitguard audit data/data.yaml --provenance data/sources.csv --recommend-splits --output reports/split-proposal
```

Use your environment's executable as shown in the [quickstart](QUICKSTART.md).

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Completed audit satisfies the selected exit policy |
| `1` | Completed audit violates that policy |
| `2` | Invalid input, missing dependency, or operational/write error |

- `confirmed`: exits 1 for byte/path overlap or reviewed source-ID conflicts.
- `any`: also exits 1 for unverified candidate findings.
- `none`: exits 0 for completed audits; input errors still exit 2.

**NOT VERIFIED can exit 0.** Missing provenance is not itself a candidate finding,
so `--fail-on any` does not require complete provenance. Integrations that require
verified independence must inspect the JSON status, checks and coverage.

## Bounds

Exact hashes stream bytes independently of similarity limits. Optional similarity
supports at most 2,000 unique images, 16,000,000 pixels per image, and 500 scored
candidate pairs. At most 1,999,000 path pairs are considered. Stopped/skipped work is
disclosed as NOT VERIFIED. A truncated result is not a global best-match ranking.

Embedded previews are capped at 8 memberships per group, 200 unique decoded images,
300 rendered previews and 8 MiB of data. All finding references remain available.

[Report guide](REPORTS.md) · [JSON contract](CONTRACTS.md) · [Documentation home](README.md)
