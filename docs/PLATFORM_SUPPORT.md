# Platform support

Python 3.10 or newer is required. The runtime depends on PyYAML and Pillow. Pillow
provides embedded report thumbnails and the optional perceptual-hash check.
The optional `similarity` extra adds NumPy for structural similarity scores.
A GPU or model runtime is not required.

## Tested environments

| Platform | Python | Installation |
|---|---|---|
| Windows | 3.10.10 | Editable package in a virtual environment |
| Windows | 3.13.7 | Installed wheel in a separate virtual environment |
| Linux | 3.10.22 | Installed wheel in an official Python slim container |
| Linux | 3.13.16 | Installed wheel in an official Python slim container |

The recorded 0.2.0a4 platform runs each passed 68 tests, including SSIM scoring. See [verification](VERIFICATION.md)
for dataset checks and the test scope. The CI workflow targets Windows and Ubuntu
with Python 3.10 and 3.13.

## Portable paths

Use forward slashes in dataset YAML and provenance CSV files. Relative dataset roots
resolve from the YAML directory, and text-list image paths resolve from the list file.
Windows absolute paths cannot be used directly on Linux; use relative paths or a
root override when moving a dataset between platforms.

The application uses standard Python filesystem APIs. Reports are UTF-8 JSON and
standalone HTML, and all scans leave source images and labels unchanged.
