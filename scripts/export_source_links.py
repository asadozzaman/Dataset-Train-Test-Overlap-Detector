"""Export verified results without redistributing dataset image files or previews."""

import argparse
import html
import json
import re
import shutil
from pathlib import Path


def export(source: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    payload = (source / "evidence.js").read_text(encoding="utf-8")
    data = json.loads(payload.removeprefix("window.SHOWCASE_EVIDENCE=").strip().removesuffix(";"))
    data["source_links_only"] = True
    references = {}
    for dataset in data["datasets"].values():
        for item in dataset["items"]:
            item["source_url"] = (
                f"https://cocodataset.org/#explore?id={int(Path(item['filename']).stem)}"
            )
            references[item["path"]] = item["source_url"]
            item["image"] = "source-preview.svg"
    check = data["filename_check"]
    check["image"] = "source-preview.svg"
    original_url = f"https://cocodataset.org/#explore?id={int(Path(check['source_filename']).stem)}"
    for member in check["members"]:
        references[member["path"]] = original_url
    for example in data["similarity_examples"]:
        for member in example["members"]:
            references[member["path"]] = member["source_url"]
            member["image"] = "source-preview.svg"

    def replace_reference(match: re.Match) -> str:
        path = html.unescape(match[1])
        url = references.get(path)
        if not url:
            return match[0]
        return (
            match[0] + f' <a href="{html.escape(url, quote=True)}" target="_blank" '
            'rel="noopener">Original source ↗</a>'
        )

    for file in source.rglob("*"):
        relative = file.relative_to(source)
        if not file.is_file() or relative.parts[0] == "assets" or file.name == "evidence.js":
            continue
        if (
            file.suffix not in {".html", ".css", ".js", ".svg", ".json", ".md", ".yaml"}
            and file.name != ".nojekyll"
        ):
            continue
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if file.suffix == ".html" and relative.parts[0] == "reports":
            content = file.read_text(encoding="utf-8")
            content = re.sub(
                r"<img\b[^>]*>",
                '<p class="preview-placeholder">Image preview omitted. '
                "Use the original source references.</p>",
                content,
            )
            sequence = "ubc" if "ubc" in file.name else "leuven" if "leuven" in file.name else None
            if sequence:
                for path, url in list(references.items()):
                    if path.startswith(sequence + "/"):
                        references[Path(path).name] = url
            content = re.sub(r"<code>([^<]+)</code>", replace_reference, content)
            destination.write_text(content, encoding="utf-8")
        else:
            shutil.copyfile(file, destination)
    (output / "evidence.js").write_text(
        "window.SHOWCASE_EVIDENCE=" + json.dumps(data, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    (output / "source-preview.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 420">'
        '<rect width="640" height="420" fill="#f1f3fa"/>'
        '<rect x="260" y="115" width="120" height="90" rx="9" fill="none" '
        'stroke="#6a7290" stroke-width="3"/>'
        '<path d="m280 185 25-28 20 20 20-15 20 23" fill="none" '
        'stroke="#6a7290" stroke-width="3"/>'
        '<text x="320" y="255" text-anchor="middle" font-family="Arial,sans-serif" '
        'font-size="23" fill="#172039">View image at its original source</text>'
        '<text x="320" y="289" text-anchor="middle" font-family="Arial,sans-serif" '
        'font-size="16" fill="#536078">This site hosts verified results '
        "and source links.</text></svg>",
        encoding="utf-8",
    )
    record_path = output / "experiments.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["publication"]["mode"] = "source_links_only"
    record["publication"]["redistributes_dataset_images"] = False
    record["publication"]["note"] = (
        "Verified results and original-source links. "
        "No dataset photos or embedded previews are included. "
        "Image redistribution rights remain unresolved."
    )
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    validate(output)


def validate(output: Path) -> None:
    for file in output.rglob("*"):
        if not file.is_file():
            continue
        if file.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ppm", ".zip"}:
            raise ValueError(f"Dataset image/archive in publication: {file.name}")
        if "data:image/" in file.read_text(encoding="utf-8"):
            raise ValueError(f"Embedded image in publication: {file.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.source, args.output)
    print(f"Verified source-link publication: {args.output}")
