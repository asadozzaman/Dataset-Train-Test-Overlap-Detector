# Third-party sources and image credits

The [MIT license](LICENSE) covers this project's code and original presentation.
It does not relicense third-party images or datasets. Source images remain outside
the source repository. The showcase build downloads selected public examples and
embeds previews or original comparison files in its deployment artifact.

## COCO, COCO8 and COCO128

COCO images originate from Flickr. Individual images retain their applicable
licenses; COCO's annotation terms and image terms are distinct. Consult the
[COCO terms of use](https://cocodataset.org/#termsofuse) and each original image's
source/license record when reusing images. An image's original numeric ID is
preserved in the showcase; its source record is linked in the COCO explorer.

Credits: the original photographers and the COCO dataset team, including the
authors of *Microsoft COCO: Common Objects in Context* (Lin et al., ECCV 2014).

- [COCO project](https://cocodataset.org/)
- [COCO128 configuration and intentional Train/Validation reuse](https://docs.ultralytics.com/datasets/detect/coco128/)
- [COCO8 configuration](https://docs.ultralytics.com/datasets/detect/coco8/)
- [Official COCO128 archive](https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip)
- [Official COCO8 archive](https://github.com/ultralytics/assets/releases/download/v0.0.0/coco8.zip)

The controlled filename example intentionally stores one COCO128 photo under two
test filenames. It is labeled as a capability check, separate from original COCO
findings. Display thumbnails are resized; the underlying official archive is unchanged.

## UBC compression and Leuven lighting benchmarks

These sequences come from the
[Oxford affine-region evaluation benchmark](https://www.robots.ox.ac.uk/~vgg/research/affine/),
distributed here through the [official OpenCV test-data repository](https://github.com/opencv/opencv_extra).
The benchmark credits its contributing research groups and publications, including
Mikolajczyk et al., *A Comparison of Affine Region Detectors*, IJCV 2005, and
Mikolajczyk and Schmid, *A Performance Evaluation of Local Descriptors*, PAMI 2005.

Original OpenCV-hosted PNG filenames and bytes are retained. Per-file source URLs,
the pinned commit, and SHA-256 fingerprints are in
[`examples/similarity_sources.json`](examples/similarity_sources.json). The project
does not create those image variations or claim ownership of them. Original-source
terms continue to apply. Example Train/Validation memberships are illustrative,
not official benchmark splits or evidence of benchmark leakage.

## Runtime dependencies

PyYAML, Pillow, and optional NumPy retain their respective upstream licenses. They
are installed as dependencies rather than copied into the source tree. The SSIM
scorer is an original implementation of published equations; scikit-image was used
as an independent verification reference and is not a runtime dependency.

The project has no affiliation with or endorsement from COCO, Ultralytics, OpenCV,
FiftyOne, Datumaro, or their maintainers.
