"""Local YOLO YAML adapter with explicit, CWD-independent path semantics."""

from pathlib import Path, PureWindowsPath

import yaml

from videosplitguard.models import Dataset, DatasetError, Sample

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
SPLITS = ("train", "val", "test")


class StrictLoader(yaml.SafeLoader):
    """Safe YAML with duplicate mapping keys rejected instead of silently replaced."""


def _unique_mapping(loader: StrictLoader, node: yaml.nodes.MappingNode) -> dict:
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise DatasetError(f"Unhashable YAML key: {key}") from exc
        if duplicate:
            raise DatasetError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def resolve_local(value: str, base: Path) -> Path:
    if "://" in value:
        raise DatasetError(f"Only local paths are supported: {value}")
    if PureWindowsPath(value).drive and not Path(value).is_absolute():
        raise DatasetError(f"This Windows path is not absolute on this host: {value}")
    path = Path(value.replace("\\", "/")).expanduser()
    return (base / path).resolve()


def _images(entry: Path) -> list[Path]:
    if not entry.exists():
        raise DatasetError(f"Missing split path: {entry}")
    if entry.is_dir():
        return sorted(
            p.resolve()
            for p in entry.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
        )
    if entry.suffix.lower() == ".txt":
        images = []
        for line in entry.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            path = resolve_local(line.strip(), entry.parent)
            if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
                raise DatasetError(f"Invalid image in {entry}: {line}")
            images.append(path)
        return images
    if entry.is_file() and entry.suffix.lower() in IMAGE_SUFFIXES:
        return [entry.resolve()]
    raise DatasetError(f"Unsupported split input: {entry}")


def load_dataset(yaml_path: Path, root_override: Path | None = None) -> Dataset:
    yaml_path = yaml_path.resolve()
    try:
        config = yaml.load(yaml_path.read_text(encoding="utf-8-sig"), Loader=StrictLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise DatasetError(f"Cannot read dataset YAML: {exc}") from exc
    if not isinstance(config, dict):
        raise DatasetError("Dataset YAML must be a mapping")
    root_value = config.get("path")
    if root_value is None:
        root_value = "."
    if not isinstance(root_value, str) or not root_value.strip():
        raise DatasetError("YAML path must be a nonempty string")
    root = root_override.resolve() if root_override else resolve_local(root_value, yaml_path.parent)
    samples, warnings = [], []
    if "download" in config:
        warnings.append(
            "YAML download directive ignored; auditing never downloads or executes code."
        )
    for split in SPLITS:
        value = config.get(split)
        if value is None or value == "":
            warnings.append(f"Split {split} is not configured.")
            continue
        entries = value if isinstance(value, list) else [value]
        if not entries or any(not isinstance(e, str) or not e.strip() for e in entries):
            raise DatasetError(f"Split {split} must be a path or nonempty list of paths")
        paths = []
        for entry in entries:
            paths.extend(_images(resolve_local(entry, root)))
        unique_paths = sorted(set(paths))
        if not unique_paths:
            raise DatasetError(f"Configured split {split} contains no supported images")
        if len(paths) != len(unique_paths):
            warnings.append(f"Repeated references within {split} were deduplicated.")
        samples.extend(Sample(path=p, split=split) for p in unique_paths)
    if len({sample.split for sample in samples}) < 2:
        raise DatasetError("At least two nonempty splits are required for a cross-split audit")
    return Dataset(yaml_path, root, tuple(samples), tuple(warnings))
