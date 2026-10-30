# Public workflow research

The similarity scorer uses the SSIM local-moment equations with uniform 7x7 windows,
sample covariance and explicit range 255. These settings are described by
[scikit-image's SSIM documentation](https://scikit-image.org/docs/stable/api/skimage.metrics.html#skimage.metrics.structural_similarity).
An independent integral-image implementation avoids a SciPy runtime dependency;
six validation pairs matched scikit-image 0.25.2 to within 1e-10. This does not
calibrate scores as probabilities or establish semantic similarity.

Real comparison images come from the UBC compression and Leuven lighting sequences
of the [Oxford affine benchmark](https://www.robots.ox.ac.uk/~vgg/research/affine/),
using the pinned files in [OpenCV's official test-data repository](https://github.com/opencv/opencv_extra).
The benchmark distinguishes compression and illumination changes. The project
preserves the downloaded bytes and filenames, and assigns example splits only for
local verification. These examples do not establish authentic cross-split leakage
or recording provenance. All images remain outside Git; source URLs and SHA-256
digests are in `examples/similarity_sources.json`.

These public workflows provide context for dataset inspection and validation.
This project focuses on evidence of overlap across dataset splits using local CPU checks.

| Source | Publicly documented workflow | Project approach |
|---|---|---|
| [FiftyOne Brain](https://docs.voxel51.com/brain/index.html) | File hashes detect exact duplicates; embedding similarity identifies near-duplicate candidates for inspection. Similarity thresholds affect false positives/negatives. | Separate exact evidence from approximate candidates; use cheap streamed SHA-256 first, no model or embedding dependency. |
| [Datumaro validate](https://open-edge-platform.github.io/datumaro/latest/docs/command-reference/validate.html) | Task-specific annotation validation writes statistics, validation findings, and a summary in JSON. | Separate machine-readable findings, statistics, and summaries; explicit warnings and errors. Annotation-quality validation is outside this project scope. |
| [CleanVision tutorial](https://cleanvision.readthedocs.io/en/stable/tutorials/tutorial.html) | Image issue summaries and inspectable duplicate sets; image counts and set counts describe different things; near-duplicate checks can use perceptual hashes. | Distinguish groups from affected memberships and unique files. Optional hashing-based near-duplicates only after core checks. |
| [Ultralytics dataset format](https://docs.ultralytics.com/datasets/detect/) | YAML supports root, split directories or text files, lists, and optional test split. | Read the small useful format surface, document path resolution differences, never execute download directives. |

## Verification sources

- [COCO8](https://docs.ultralytics.com/datasets/detect/coco8/): 8 COCO images, 4 train and 4 validation. Useful small baseline, not proof of scene or video independence.
- [COCO128](https://docs.ultralytics.com/datasets/detect/coco128/): same 128 images assigned to train and validation intentionally for debugging. Expected positive exact-overlap test.
- Official archives: [COCO8 ZIP](https://github.com/ultralytics/assets/releases/download/v0.0.0/coco8.zip), [COCO128 ZIP](https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip).
- [COCO terms](https://cocodataset.org/#termsofuse): dataset/image terms are distinct from this project's MIT code license. Download only for local verification; do not bundle images into the source repository or imply MIT relicensing.

The script records archive SHA-256 and run time for reproducibility. These are observed
checksums of downloaded artifacts, not independently authenticated upstream checksums.
The release URLs are stable names but remote bytes could change; count assertions and
recorded digests make unexpected changes visible.

COCO image IDs do not establish video or session origin. Controlled metadata fixtures
will test group logic separately and must be labeled synthetic. Real-world validation
of provenance inference needs a future dataset with trustworthy source-video/session
metadata; it is not claimed by COCO verification.
