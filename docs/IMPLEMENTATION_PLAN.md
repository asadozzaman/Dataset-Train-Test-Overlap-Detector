# Development status

Core functionality is implemented. This checklist tracks supported behavior,
verification coverage, and possible future improvements.

| Stage | Result |
|---|---|
| Environment and public workflow research | Completed; Python 3.10/3.13, Git, VS Code; FiftyOne/Datumaro/CleanVision/YOLO documents reviewed |
| Package and exact engine | Completed; installable package, deterministic YOLO paths, SHA-256 overlap |
| Provenance engine | Completed; strict CSV, verified/candidate separation, video and session groups |
| CLI and reports | Completed; `audit`, exit policies, structured JSON, standalone HTML, recommendations |
| Optional features | Completed; bounded dHash + SSIM candidates and non-destructive group-aware proposal |
| Verification | 63 tests each on Windows and Linux Python 3.10/3.13; real COCO runs on both OSes, synthetic provenance, package build and browser render |

## Core acceptance

- [x] YOLO `path`/`train`/`val`/`test` directories, files, lists and text manifests.
- [x] Shared-path and byte-identical cross-split findings; within-split duplicates do
      not count as leakage.
- [x] Strict provenance CSV with root-relative joins, required evidence values and
      source references, conflict checks and unused-row warnings.
- [x] Independently detect source-video and recording-session overlap.
- [x] Missing, partial and unreviewed source IDs remain NOT VERIFIED; mixed evidence
      cannot upgrade unreviewed members.
- [x] CLI `videosplitguard audit`, documented 0/1/2 exit codes and policies.
- [x] JSON 0.2 and escaped standalone HTML agree on findings and coverage.
- [x] Actionable recommendations based on observed findings.
- [x] Stable report bytes for unchanged inputs at identical paths; no timestamp.
- [x] Invalid paths/configuration/empty splits fail closed; no successful clean report.
- [x] Synthetic tests for same video, different videos in one session, partial data,
      mixed evidence, conflicts, unused rows and three-split membership unions.
- [x] Streaming hash with a per-file mutation check.
- [x] Automated tests, lint/format, package build and real public-data verification.
- [x] Reject truncated CSV records and report safe image-decoding failures gracefully.
- [x] Stage report artifacts, publish JSON last and roll back ordinary publication failures.
- [x] Preserve shared-path evidence in mixed groups containing renamed copies.

## Optional acceptance

- [x] CPU dHash candidates through Pillow, explicit threshold and caps: 2,000
      images, 16 million pixels/image, 500 candidate groups, <=1,999,000 comparisons.
- [x] Group-aware proposed membership CSV keeps exact and verified source groups
      together, discloses ratio deviation and never mutates source data.
- [x] Embedded image previews with split labels, full member references, original-file
      links, bounded report size, and readable fallback placeholders.

## Remaining verification and later refinements

- [x] Execute the supported platform/version matrix locally: Windows and Linux,
      Python 3.10 and 3.13, with 63 tests passing in each combination.
- [ ] Run the configured GitHub Actions workflow on the hosted repository.
      Local test results are recorded separately from hosted CI.
- [ ] Test larger real video datasets with authentic reviewed source manifests. COCO
      has no verified video/session records, so these checks use labeled synthetic data.
- [ ] Consider explicit filename regex hints if users need them. Do not infer source IDs
      from default names, especially numeric COCO filenames.
- [ ] Consider crash-atomic output and a frozen-dataset snapshot contract. Ordinary
      report failures now roll back staged/published artifacts; abrupt termination or
      rollback errors can still leave incomplete output. Per-file stat checks catch
      changes only during hashing.
- [ ] Consider class-balance constraints for proposals only with a defined label
      analysis scope. Current proposal reports approximate ratios and does not assess
      labels or visual contents.

## Release gate

Local Windows and Linux verification passed for version 0.2.0a3. Real source-manifest
field validation remains a future verification task. Dataset archives, third-party
images, generated reports, and virtual environments are excluded from source control.

## Similarity comparisons (0.2.0a4)

- [x] Defined structural-similarity and 64-bit perceptual-agreement scores in JSON/HTML.
- [x] Preserve candidate status; disclose normalization, alignment/color limits and low detail.
- [x] Bound SSIM work to 500 comparisons and keep NumPy an optional dependency.
- [x] Check SSIM against direct-window mathematics and an independent library reference.
- [x] Show intact, checksum-verified UBC/Leuven files from OpenCV with original filenames.
- [x] Disclose illustrative split memberships; do not claim benchmark leakage or provenance.
- [x] Link comparison images, source URLs, file hashes and real HTML/JSON audits.
- [x] Verify engine tests on Windows/Linux and Python 3.10/3.13; verify showcase interactions.
- [ ] Review current showcase layout in an enabled browser at desktop/mobile widths.
