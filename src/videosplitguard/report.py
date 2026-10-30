"""Deterministic offline JSON and HTML reports with escaped user-supplied text."""

import csv
import html
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from videosplitguard.previews import ImagePreviews, select_members


def _reference(member: dict, previews: ImagePreviews) -> str:
    escape = html.escape
    source = previews.source_path(member["path"])
    details = (
        f"<strong>{escape(member['split'].upper())}</strong> · "
        f"<code>{escape(member['path'])}</code>"
    )
    if "evidence" in member:
        details += f"<br><small>Metadata: {escape(member['evidence'])}"
        if member["source_ref"]:
            details += f" · reference: {escape(member['source_ref'])}"
        details += "</small>"
    if "sha256" in member:
        details += f"<br><small>SHA-256: <code>{escape(member['sha256'])}</code></small>"
    return (
        details
        + f'<br><a class="source-link" href="{escape(source.as_uri(), quote=True)}" '
        + 'target="_blank" rel="noopener">Open original image</a>'
    )


def _finding_gallery(finding: dict, number: int, previews: ImagePreviews, badge) -> str:
    escape = html.escape
    explanations = {
        "exact_overlap": (
            "The same image content appears in different splits. "
            "Compare the previews and file references below."
        ),
        "source_video_overlap": (
            "These images share a video ID in the supplied metadata. "
            "Different frames need not look identical."
        ),
        "recording_session_overlap": (
            "These images share a recording-session ID in the supplied metadata. "
            "Grouping is based on the source records."
        ),
        "near_duplicate_candidate": (
            "These images have similar perceptual hashes. "
            "Review them visually; this is an unverified candidate."
        ),
    }
    cards = []
    selected = select_members(finding["members"])
    for member in selected:
        source = previews.source_path(member["path"])
        preview = previews.get(source)
        if preview.data_url:
            alt = escape(f"{member['split']}: {member['path']}", quote=True)
            visual = (
                f'<img src="{preview.data_url}" alt="{alt}" width="384" height="256" '
                'loading="lazy" decoding="async">'
            )
        else:
            visual = (
                '<div class="preview-placeholder">'
                + escape(preview.message or "Preview unavailable")
                + "</div>"
            )
        cards.append(
            '<figure class="image-card">'
            f'<div class="image-label {escape(member["split"])}">'
            f"{escape(member['split'].upper())}</div>"
            + visual
            + f"<figcaption>{_reference(member, previews)}</figcaption></figure>"
        )
    remaining = ""
    if len(selected) < len(finding["members"]):
        references = "".join(f"<li>{_reference(m, previews)}</li>" for m in finding["members"])
        remaining = (
            f"<p>Showing {len(selected)} of {len(finding['members'])} memberships, "
            "sampled across splits.</p>"
            f"<details><summary>All {len(finding['members'])} image references</summary>"
            f"<ul>{references}</ul></details>"
        )
    shared = ""
    metric = ""
    if finding.get("similarity"):
        score = finding["similarity"]
        metric = (
            '<div class="similarity-metrics">'
            f"<p><strong>Structural similarity (SSIM): "
            f"{score['structural_similarity_percent']:.2f}%</strong> · "
            f"dHash agreement: {score['hash_agreement_percent']:.2f}% "
            f"({score['dhash_distance']}/64 bits differ)</p>"
            f"<p>{escape(score['note'])}</p>"
            + (
                "<p><strong>Low-information image:</strong> flat or low-detail images "
                "can have high scores without being duplicates.</p>"
                if score["low_information"]
                else ""
            )
            + "<p><strong>Action:</strong> inspect scene details and source records. "
            "If these are related captures, keep the source group in one split.</p></div>"
        )
    if finding.get("shared_paths"):
        shared = (
            "<p><strong>Shared across splits:</strong> "
            + ", ".join(f"<code>{escape(path)}</code>" for path in finding["shared_paths"])
            + "</p>"
        )
    return (
        f'<article class="finding" id="finding-{number}"><div class="finding-heading">'
        + f"<h3>Group {number}: {escape(finding['kind'].replace('_', ' ').title())}</h3>"
        + badge(finding["status"])
        + "</div>"
        + f"<p>{escape(explanations[finding['kind']])}</p>"
        + f"<p><strong>Evidence:</strong> {escape(finding['evidence'])} · "
        + f"<strong>Splits:</strong> {escape(', '.join(finding['splits']))}</p>"
        + "<details class='group-id'><summary>Image hash / source ID</summary>"
        + f"<code>{escape(finding['group_id'])}</code></details>"
        + shared
        + metric
        + '<div class="image-gallery">'
        + "".join(cards)
        + "</div>"
        + remaining
        + "</article>"
    )


def render_html(report: dict) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value), quote=True)

    def badge(status: str) -> str:
        style = {"PASS": "pass", "FAIL": "fail", "NOT VERIFIED": "unknown"}[status]
        return f'<span class="badge {style}">{esc(status)}</span>'

    summary = report["summary"]
    checks = "".join(
        f"<tr><th>{esc(name.replace('_', ' ').title())}</th><td>{badge(status)}</td></tr>"
        for name, status in report["checks"].items()
    )
    near = report["optional_checks"]["near_duplicates"]
    optional_check = (
        f"<tr><th>Near duplicates (optional)</th><td>{esc(near['status'])}"
        f" · {near['images_considered']} images · {near['comparisons']} comparisons</td></tr>"
    )
    split_counts = " · ".join(
        f"{esc(split)}: {count}" for split, count in summary["split_memberships"].items()
    )
    previews = ImagePreviews(Path(report["dataset"]["root"]))
    finding_rows = (
        "".join(
            _finding_gallery(finding, number, previews, badge)
            for number, finding in enumerate(report["findings"], start=1)
        )
        or "<p>No cross-split groups found in the completed checks.</p>"
    )
    preview_note = (
        f"{previews.rendered} embedded previews. Up to 8 memberships per group, 200 unique "
        "images, 300 rendered previews, and 8 MiB of embedded image data per report. "
        "All image references remain available even when previews are limited."
    )
    if previews.omitted or previews.unavailable:
        preview_note += (
            f" {previews.omitted} preview(s) omitted by limits; "
            f"{len(previews.unavailable)} source image(s) unavailable for preview."
        )
    coverage_rows = "".join(
        f"<tr><th>{esc(kind.title())}</th><td>{counts['verified_memberships']}</td>"
        f"<td>{counts['unverified_memberships']}</td>"
        f"<td>{counts['missing_memberships']}</td></tr>"
        for kind, counts in (
            ("video", report["provenance"]["video"]),
            ("session", report["provenance"]["session"]),
        )
    )
    recommendations = "".join(f"<li>{esc(item)}</li>" for item in report["recommendations"])
    notes = "".join(f"<li>{esc(item)}</li>" for item in report["warnings"] + report["limitations"])
    split_plan = report["split_recommendations"]
    if split_plan:
        proposed_counts = "".join(
            f"<tr><th>{esc(split)}</th><td>{split_plan['target_counts'][split]}</td>"
            f"<td>{count}</td><td>{split_plan['deviation_counts'][split]:+g}</td></tr>"
            for split, count in split_plan["proposed_counts"].items()
        )
        plan_notes = "".join(f"<li>{esc(note)}</li>" for note in split_plan["notes"])
        plan_warnings = "".join(f"<li>{esc(note)}</li>" for note in split_plan["warnings"])
        plan_section = (
            "<section class='card'><h2>Proposed splits</h2>"
            f"<p><strong>{esc(split_plan['status'])}</strong></p>"
            f"<p>{split_plan['component_count']} source groups · "
            f"{split_plan['removed_memberships']} memberships to remove · "
            f"{split_plan['new_assignments']} new assignments</p>"
            "<div class='table-wrap'><table><thead><tr><th>Split</th><th>Target</th>"
            "<th>Proposed</th><th>Difference</th></tr></thead>"
            f"<tbody>{proposed_counts}</tbody></table></div>"
            f"<p>See <code>{esc(split_plan['file'])}</code> for every image.</p>"
            f"<ul>{plan_warnings}</ul>"
            f"<ul>{plan_notes}</ul></section>"
        )
    else:
        plan_section = ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(report["tool"]["name"])} · {esc(report["status"])}</title>
<style>
:root {{color-scheme:light;--ink:#17263c;--sub:#53637a;--line:#dce5ef;--blue:#164b83}}
* {{box-sizing:border-box}} body {{margin:0;background:#f4f7fb;color:var(--ink);
font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main {{max-width:1120px;margin:auto;padding:28px 22px 64px}}
header {{background:#122d50;color:white;padding:30px;border-radius:14px;margin-bottom:22px}}
h1 {{font-size:2rem;margin:0 0 6px}} h2 {{font-size:1.18rem;margin:0 0 14px}}
h3 {{font-size:1.08rem;margin:0}}
header p {{margin:4px 0;color:#d7e4f4}} .card {{background:white;border:1px solid var(--line);
border-radius:12px;padding:22px;margin:17px 0;box-shadow:0 2px 7px #173a6010}}
.jump-link {{display:inline-block;margin-top:15px;background:white;color:#173b67;
padding:8px 13px;border-radius:7px;font-weight:650;text-decoration:none}}
.grid {{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}}
.metric {{padding:16px;background:#f2f6fb;border-radius:9px}} .metric b {{display:block;
font-size:1.65rem;line-height:1.3;color:var(--blue)}} .metric small,small {{color:var(--sub)}}
.badge {{display:inline-block;font-size:.78rem;font-weight:750;letter-spacing:.04em;
padding:4px 9px;border-radius:999px;white-space:nowrap}}
.pass {{background:#e4f5e9;color:#126036}} .fail {{background:#fee7e5;color:#a52626}}
.unknown {{background:#fff0d3;color:#87550c}}
table {{width:100%;border-collapse:collapse}}
th,td {{padding:11px 12px;border-bottom:1px solid var(--line);
text-align:left;vertical-align:top;overflow-wrap:anywhere}}
thead th {{background:#edf3fa}} .table-wrap {{overflow-x:auto}} code {{word-break:break-all}}
.finding {{border-top:1px solid var(--line);padding:24px 0}}
.finding-heading {{display:flex;justify-content:space-between;align-items:center;gap:12px}}
.image-gallery {{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
gap:16px;margin-top:16px}}
.image-card {{margin:0;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.image-label {{font-size:.8rem;font-weight:750;padding:7px 13px;letter-spacing:.04em}}
.image-label.train {{background:#def2e6;color:#155837}}
.image-label.val {{background:#e2edff;color:#234f8e}}
.image-label.test {{background:#efe3ff;color:#65408d}}
.image-card img {{display:block;width:100%;height:230px;object-fit:contain;background:#eff3f8}}
.image-card figcaption {{padding:13px;font-size:.85rem;overflow-wrap:anywhere}}
.preview-placeholder {{min-height:230px;display:flex;align-items:center;padding:20px;
background:#f2f5fa;color:var(--sub)}}
.source-link {{font-size:.82rem;color:var(--blue)}} .group-id {{font-size:.82rem}}
summary {{cursor:pointer}} li {{margin-bottom:7px}}
@media(max-width:560px) {{main {{padding:14px}} header {{padding:20px}}
h1 {{font-size:1.5rem}} .finding-heading {{align-items:flex-start}}}}
footer {{font-size:.86rem;color:var(--sub);overflow-wrap:anywhere}}
</style></head><body><main>
<header><h1>{esc(report["tool"]["name"])}</h1><p>Dataset split leakage audit</p>
<p>Overall result: {badge(report["status"])}</p>
<a class="jump-link" href="#visual-evidence">View overlap images</a></header>
<section class="card" aria-label="Summary"><h2>Summary</h2><div class="grid">
<div class="metric"><b>{summary["confirmed_exact_groups"]}</b>
<small>Exact image groups</small></div>
<div class="metric"><b>{summary["confirmed_video_groups"]}</b>
<small>Confirmed video groups</small></div>
<div class="metric"><b>{summary["confirmed_session_groups"]}</b>
<small>Confirmed session groups</small></div>
<div class="metric"><b>{summary["candidate_groups"]}</b><small>Unverified candidates</small></div>
</div><p>{summary["unique_files"]} unique image paths · {summary["affected_memberships"]}
affected split memberships · {esc(split_counts)}</p></section>
<section class="card"><h2>Check status</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Result</th></tr></thead>
<tbody>{checks}{optional_check}</tbody></table></div></section>
<section class="card"><h2>Source provenance coverage</h2>
<p>{esc(report["provenance"]["evidence_note"])}</p><div class="table-wrap"><table>
<thead><tr><th>Source</th><th>Verified memberships</th>
<th>Unverified</th><th>Missing</th></tr></thead>
<tbody>{coverage_rows}</tbody></table></div></section>
<section class="card" id="visual-evidence"><h2>Visual overlap evidence</h2>
<p><small>{esc(preview_note)}</small></p>{finding_rows}</section>
<section class="card"><h2>Recommended next steps</h2><ol>{recommendations}</ol></section>
{plan_section}
<section class="card"><h2>Warnings and limits</h2><ul>{notes}</ul></section>
<footer>Schema {esc(report["schema_version"])} ·
{esc(report["tool"]["name"])} {esc(report["tool"]["version"])}
<br>Dataset: {esc(report["dataset"]["yaml"])}
<br>Provenance: {esc(report["dataset"]["provenance_csv"] or "none")}</footer>
</main></body></html>"""


def _write_artifacts(report: dict, output: Path) -> None:
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "report.html").write_text(render_html(report), encoding="utf-8")
    plan = report["split_recommendations"]
    if plan:
        with (output / plan["file"]).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=["path", "current_splits", "proposed_split", "component_id"]
            )
            writer.writeheader()
            writer.writerows(plan["rows"])


def write_reports(report: dict, output: Path) -> None:
    """Stage all artifacts first, reserve a new directory, and publish JSON last.

    An ordinary write/move failure rolls back files published by this call. This is
    not a crash-atomic directory transaction: killing the process can interrupt it.
    """
    output = output.absolute()
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{output.name}-", suffix=".tmp", dir=output.parent) as folder:
        stage = Path(folder)
        _write_artifacts(report, stage)
        artifacts = ["report.html"]
        if report["split_recommendations"]:
            artifacts.append("suggested_splits.csv")
        artifacts.append("report.json")
        # Exclusive creation preserves an output created by another process while staging.
        output.mkdir(exist_ok=False)
        published = []
        try:
            for name in artifacts:
                destination = output / name
                (stage / name).replace(destination)
                published.append(destination)
        except BaseException:
            for destination in reversed(published):
                destination.unlink(missing_ok=True)
            output.rmdir()
            raise
