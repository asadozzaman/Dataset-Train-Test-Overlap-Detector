# Showcase deployment

The public showcase is a static GitHub Pages site:

**https://asadozzaman.github.io/Dataset-Train-Test-Overlap-Detector/**

It displays measured examples and downloadable public reports. It does not run a
Python service or accept uploads. Users audit new datasets with the local CLI.

## Publication modes

The deployed edition contains verified measurements, configurations and original-source
links. It includes no dataset photos or embedded previews. The local full build retains
image previews while source redistribution terms and attribution remain unresolved.

After building and testing the full site, the workflow runs:

```text
python scripts/export_source_links.py --source reports/showcase --output reports/showcase-public
```

The exporter preserves measurements and replaces photo references with an original
project SVG explaining how to open the source. Standalone reports omit embedded
previews and link to original source records. An artifact scan rejects raster images,
archives and embedded image data. Only `reports/showcase-public/` is uploaded.

`experiments.json` records `mode: source_links_only`,
`redistributes_dataset_images: false`, and `rights_verified: false`. The last flag
remains false because image permissions have not been established. This export
mode does not grant or claim third-party redistribution permission.

## Automatic publication

[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) runs on pushes to
`main` and can be dispatched from the Actions tab. It:

1. Installs the Python package and test tools.
2. Runs lint, formatting and pytest checks.
3. Downloads official COCO archives and verifies their expected results.
4. Fetches pinned, checksum-verified OpenCV benchmark files.
5. Runs the real audit engine to build the showcase and its public HTML/JSON reports.
6. Runs the showcase's Node/jsdom interaction checks.
7. Exports a source-link edition and verifies that it contains no dataset photos.
8. Uploads only `reports/showcase-public/`, then deploys that artifact to Pages.

Generated images, archives, personal datasets, virtual environments and local reports
stay outside Git history. The build artifact contains the deliberately selected public
dataset examples. The source repository retains its source manifests and credits.
Public report copies remove local machine paths and original-file links.

Pages must use **GitHub Actions** as its publishing source in repository Settings →
Pages. The deploy job receives `pages: write` and `id-token: write`; source contents
remain read-only for the workflow. Deployment is restricted to `main` pushes/manual
dispatches; pull requests run the separate test matrix.

## Build locally

After installing `.[dev,similarity]` into your environment:

```powershell
.\.venv\Scripts\python.exe scripts\verify_public_datasets.py --download --output reports\local-public-check
.\.venv\Scripts\python.exe scripts\fetch_similarity_examples.py
.\.venv\Scripts\python.exe scripts\build_showcase.py --output reports\local-showcase --github-url https://github.com/asadozzaman/Dataset-Train-Test-Overlap-Detector
.\.venv\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1 --directory reports\local-showcase
```

Use new output directories when rebuilding. The build script reuses cached archives.
It exports `experiments.json`, four portable YAML configurations, real reports,
resized COCO previews and byte-preserved benchmark PNGs. The 39 KB evidence index
references separate images; the initial JavaScript no longer embeds every image.
In another terminal, from `showcase/`, run:

```powershell
npm ci
$env:SHOWCASE_OUTPUT = "..\reports\local-showcase"
npm test
npm run test:browser
```

The optional browser suite uses installed Google Chrome through `playwright-core`.
To use another Chromium executable, set `SHOWCASE_BROWSER` to its absolute path.
No browser download or runtime website dependency is introduced. The test serves
the build under `/Dataset-Train-Test-Overlap-Detector/` on a temporary local port,
checks widths 320, 390, 768, 1024 and 1440, runs axe WCAG A/AA rules, and saves
screenshots/accessibility records alongside the build in `browser/`. `npm test`
does not require a browser. These are automated checks, not accessibility certification.

`SHOWCASE_OUTPUT` is resolved by Node's filesystem from the test process directory.
Use an absolute path if the output lives elsewhere. On Linux, set the same variable
with `SHOWCASE_OUTPUT=/absolute/path npm test`.

## Verify a deployment

Check the `showcase` Actions run and its deployment URL. Then inspect:

- The root page and image explorer.
- The similarity examples, original source links and score changes.
- `reports/coco128.html` and `reports/coco8.html`.
- `reports/similarity-ubc.html` and their JSON downloads.
- `credits.html` and repository links.

Browser QA on 2026-10-31 covered desktop/mobile layouts and interactions; the prior
DOM-only verification limit has been addressed for this local revision.
Dataset/source-provenance boundaries remain
the same on the hosted site. Read [third-party notices](../THIRD_PARTY_NOTICES.md)
before republishing dataset images.
