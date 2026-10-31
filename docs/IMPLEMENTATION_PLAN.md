# Development status

## Active Phase 1 — 2026-10-31

Purpose and constraints: [PROJECT_GOAL.md](../PROJECT_GOAL.md). Evidence ledger:
[RESEARCH_EVIDENCE.md](../RESEARCH_EVIDENCE.md). Reuse this checklist for continuation.

- [x] Inspect clean working tree, engine, CLI, configuration, reports, tests,
      existing vanilla HTML/CSS/JS site and GitHub Pages workflow.
- [x] Rerun official COCO audits and verify all pinned benchmark image checksums.
- [x] Present all four experiments prominently with accurate evidence boundaries.
- [x] Export compact experiment/configuration records and improve asset loading.
- [x] Improve research/local-use guidance and responsive, accessible presentation.
- [x] Run Python, build, interaction and real browser validation (see verification log).
- [ ] Resolve image redistribution terms and attribution before public deployment.

Assessment: functional engine and measured showcase already exist. The minimal
implementation keeps the stack, strengthens the visitor narrative, reuses the
image inspector and similarity controls, and adds an inspectable experiment
record. No engine redesign or Phase 2 work is needed. Risks: unverified source
rights, absent recording histories, and previously unreviewed mobile layouts.
Implemented: original indigo/teal design, four linked findings, existing evidence
controls, local commands, methods/limits, downloadable configurations and compact
experiment metadata. Images load separately; benchmark bytes remain unchanged.
Verified: 68 Python tests, 12 DOM tests, five Chrome widths and axe checks, keyboard
dialog/tabs, project-path links, lint/format and wheel/sdist build. Engine unchanged.
COCO128 comprehension follow-up: added a shared-folder overview showing 128 unique
images used by both splits, explicit Train/Validation paths for the selected file,
and dataset-specific explorer headings. Repeated filenames now have a direct
explanation. Updated source and the running local build; all 12 DOM checks and
five-width Chrome/accessibility checks passed. Phase 1 scope is unchanged.
Visual comparison follow-up: the primary evidence section now has four accessible
cases (renamed photo, compression, lighting, separate images). It shows Train and
Validation originals before the audit result and plain-language interpretation.
Technical evidence is disclosed on demand; full COCO datasets and extra benchmark
pairs remain in an expandable library. Controlled and illustrative setups are
explicit. No unmeasured crop/color claims were introduced. Updated the running
local build. Verification: 13 DOM checks and all 8 Chrome subchecks passed,
including five widths and axe checks for every new case. Engine/results unchanged.
Next action: resolve and record source permissions/attribution before publication.
Phase 1 remains on track; release acceptance is incomplete until that evidence exists.

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


## Source-link release — 2026-10-31

Owner authorized push/deployment and selected a public edition with original-source
links instead of hosted photos. Added a separate export and publication verification;
kept the full local preview build. Fresh Python suite: 68 passed; showcase DOM: 13
passed; public export checks: 2 passed; lint passed. Image redistribution remains
unresolved and is not represented as approved. Next: push and verify Pages deployment.
