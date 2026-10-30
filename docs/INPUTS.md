# Inputs and provenance

## YOLO YAML

Supported keys are `train`, `val`, and `test`. A split can name a directory, individual
image, `.txt` manifest, or a list of those:

```yaml
path: ../datasets/inspection
train:
  - images/train
  - additional-train.txt
val: validation.txt
test: images/test
```

Path resolution:

1. A relative `path` resolves from the YAML file's directory.
2. Split entries resolve from the dataset root.
3. Lines inside a text manifest resolve from the **manifest's directory**.
4. `--root` overrides the dataset root.

Use forward slashes for portable YAML/CSV. Directories are scanned recursively;
JPG, JPEG, PNG, BMP, WebP, TIF, and TIFF are supported case-insensitively.
At least two splits must contain images. Missing configured paths and empty
configured splits fail with readable errors. Repeated references inside one split
are collapsed with a warning; cross-split references remain overlap evidence.
Duplicate YAML keys are rejected. Download directives are ignored.

## Source provenance

All CSV columns are required:

| Column | Meaning |
|---|---|
| `path` | Unique dataset-root-relative image path, including directories |
| `video_id` | Globally consistent source-video ID; blank means unknown |
| `session_id` | Globally consistent recording-session ID; blank means unknown |
| `evidence` | `verified` or `unverified` |
| `source_ref` | Reviewed source reference; required for a verified row |

Illustrative records — **not authentic recording histories**:

```csv
path,video_id,session_id,evidence,source_ref
images/train/frame_001.jpg,inspection/session01/video_a,inspection/session01,verified,reviewed-export-manifest
images/val/frame_080.jpg,inspection/session01/video_a,inspection/session01,verified,reviewed-export-manifest
images/test/unknown.jpg,,,unverified,
```

The first two rows establish a conflict **in supplied reviewed assertions**. The tool
does not authenticate their source or reconstruct recording history. Use export
logs, recording manifests or other records you actually reviewed. Filename patterns
are insufficient proof.

Missing rows/IDs and unreviewed records keep the relevant check NOT VERIFIED. In
mixed-evidence groups, only the reviewed cross-split subset forms a confirmed
metadata finding; unreviewed members stay candidates.

CSV paths cannot escape the root or use URLs. Duplicate paths/columns, missing
fields and conflicting video-to-session mappings are rejected. Unused rows warn.
Qualify IDs across collections/cameras that might reuse local names.

YOLO labels, model weights, a GPU and training are unnecessary. Missing source
records cannot produce verified source independence. Label quality and class
balance are outside the checks.

[Quickstart](QUICKSTART.md) · [Report contract](CONTRACTS.md) · [Documentation home](README.md)
