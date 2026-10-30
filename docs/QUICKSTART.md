# Quickstart

## Install

Python 3.10+ and Git are required:

```bash
git clone https://github.com/asadozzaman/Dataset-Train-Test-Overlap-Detector.git
cd Dataset-Train-Test-Overlap-Detector
python -m venv .venv
```

Use `python3` on Linux if needed. Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[similarity]"
.\.venv\Scripts\videosplitguard.exe --version
```

Linux:

```bash
.venv/bin/python -m pip install '.[similarity]'
.venv/bin/videosplitguard --version
```

The explicit executable path avoids activation problems. The similarity extra adds
NumPy; install `.` for exact/source checks alone. Installation is from the checkout;
there is no published PyPI release yet.

## Configure your dataset

```text
my-dataset/
├── data.yaml
└── images/
    ├── train/
    ├── val/
    └── test/
```

```yaml
# my-dataset/data.yaml
train: images/train
val: images/val
test: images/test
```

Omit `test` when absent. At least two splits must contain images. Labels are not
required. See [input rules](INPUTS.md) for manifests and root overrides.

## Run and inspect

Windows:

```powershell
.\.venv\Scripts\videosplitguard.exe audit "path\to\data.yaml" --near-duplicates --output "reports\my-audit"
```

Linux:

```bash
.venv/bin/videosplitguard audit path/to/data.yaml --near-duplicates --output reports/my-audit
```

Replace the configuration path with your own and use a new output directory.
Open `reports/my-audit/report.html`; structured results are in `report.json`.
Embedded previews work offline. **Exit 1 for confirmed overlap is an expected
audit result, not an application crash.**

Without source records, video/session status remains NOT VERIFIED. High-scoring
similarity pairs also remain NOT VERIFIED. Read the [report guide](REPORTS.md).

Add reviewed [provenance records](INPUTS.md#source-provenance) using:

```powershell
.\.venv\Scripts\videosplitguard.exe audit "path\to\data.yaml" --provenance "path\to\sources.csv" --output "reports\with-sources"
```

Only use `verified` after reviewing the cited record. Filename patterns alone are
insufficient evidence of a common source video or session.

## Try official public data

No personal dataset is needed to reproduce the included checks:

```powershell
.\.venv\Scripts\python.exe scripts\verify_public_datasets.py --download --output reports\public-run
```

Expected results:

- **COCO128:** 128 intentional Train/Validation exact-overlap groups.
- **COCO8:** zero exact-overlap groups; 4 Train and 4 Validation images.
- **Synthetic provenance regression:** one video and one session group, explicitly test-only.
- **Injected-copy regression:** one confirmed byte-overlap group in an isolated copy.

Reports are under `reports/public-run/`; cached official archives are in `data/public/`.
Both are Git-ignored. Choose another output folder to rerun; cached downloads are
reused. The audit CLI never downloads data by itself.

## Troubleshooting

| Behavior | Action |
|---|---|
| Command not found | Use the virtual environment's executable path above |
| Output already exists | Choose a new `--output` directory |
| Missing image/directory | Check YAML paths from its configuration/root and manifest lines from their manifest folder |
| Fewer than two nonempty splits | Supply at least two image splits |
| NumPy required | Install `.[similarity]` into the same Python environment |
| Similarity skipped at size limit | Inspect the disclosed bound; exact/source checks have separate results |
| No exact overlap, but overall NOT VERIFIED | Supply reviewed video/session provenance |
| Original links break after moving HTML | Previews remain embedded; original links refer to the original dataset location |

[CLI reference](CLI.md) · [Report guide](REPORTS.md) · [Documentation home](README.md)
