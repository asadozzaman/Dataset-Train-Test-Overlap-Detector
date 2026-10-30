"""Small standard-library CLI; errors cannot masquerade as successful audits."""

import argparse
import sys
from pathlib import Path

from videosplitguard import __version__
from videosplitguard.audit import audit
from videosplitguard.models import DatasetError
from videosplitguard.report import write_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="videosplitguard")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "scan"):
        command = commands.add_parser(name, help="Audit local YOLO dataset split leakage")
        command.add_argument("dataset", type=Path, help="YOLO dataset YAML")
        command.add_argument("--root", type=Path, help="Override dataset root")
        command.add_argument("--provenance", type=Path, help="Optional source provenance CSV")
        command.add_argument(
            "--near-duplicates", action="store_true", help="Check bounded perceptual candidates"
        )
        command.add_argument(
            "--near-threshold", type=int, default=None, help="dHash distance (0-64)"
        )
        command.add_argument(
            "--recommend-splits", action="store_true", help="Write non-destructive split proposal"
        )
        command.add_argument("--output", type=Path, required=True, help="New report directory")
        command.add_argument("--fail-on", choices=["confirmed", "any", "none"], default="confirmed")
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise DatasetError(f"Output already exists; choose a new directory: {args.output}")
        if args.near_threshold is not None and not args.near_duplicates:
            raise DatasetError("--near-threshold requires --near-duplicates")
        report = audit(
            args.dataset,
            args.root,
            args.provenance,
            near_duplicates=args.near_duplicates,
            near_threshold=args.near_threshold if args.near_threshold is not None else 6,
            recommend_splits=args.recommend_splits,
        )
        write_reports(report, args.output)
    except (DatasetError, OSError, UnicodeError) as exc:
        print(f"videosplitguard: error: {exc}", file=sys.stderr)
        return 2
    summary = report["summary"]
    confirmed = (
        summary["confirmed_exact_groups"]
        + summary["confirmed_video_groups"]
        + summary["confirmed_session_groups"]
    )
    print(
        f"{report['status']}: {confirmed} confirmed groups, "
        f"{summary['candidate_groups']} candidates"
    )
    print(f"JSON: {(args.output / 'report.json').resolve()}")
    print(f"HTML: {(args.output / 'report.html').resolve()}")
    if report["split_recommendations"]:
        plan = report["split_recommendations"]
        print(f"Proposal ({plan['status']}): {(args.output / 'suggested_splits.csv').resolve()}")
        for warning in plan["warnings"]:
            print(f"Proposal warning: {warning}")
    return int(
        (args.fail_on == "confirmed" and confirmed > 0)
        or (args.fail_on == "any" and bool(report["findings"]))
    )
