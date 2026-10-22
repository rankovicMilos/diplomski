"""
Command line interface for running the config-driven scrapers locally.

Run from backend/scraper-lambda:

    uv run python -m src.services.scraping.cli list
    uv run python -m src.services.scraping.cli list --industry electricity --status all
    uv run python -m src.services.scraping.cli validate
    uv run python -m src.services.scraping.cli run --source-id aers-annual-report-2024
    uv run python -m src.services.scraping.cli run --industry fuel
    uv run python -m src.services.scraping.cli run --strategy live --force
    uv run python -m src.services.scraping.cli run --all
    uv run python -m src.services.scraping.cli run --status blocked --all   # retry blocked ones

Output goes to ./output (mirrors the S3 key layout) unless --storage s3 is given.
A JSON report of every run is written to ./output/_reports/.
"""
import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from .core.exceptions import ConfigError
from .core.models import SourceStatus
from .core.storage import StorageFactory
from .runner import load_registry, run_sources

STATUS_CHOICES = ["active", "all"] + [s.value for s in SourceStatus if s != SourceStatus.ACTIVE]


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        registry = load_registry(Path(args.config_dir) if args.config_dir else None)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 2

    if args.command == "validate":
        counts = Counter(s.status.value for s in registry)
        print(f"OK: {len(registry)} sources. By status: {dict(counts)}")
        return 0

    statuses = _statuses(args.status)
    configs = registry.filter(
        source_ids=args.source_id or None,
        industry=args.industry,
        strategy=args.strategy,
        statuses=statuses,
    )

    if args.command == "list":
        _print_sources(configs)
        return 0

    if not (args.all or args.source_id or args.industry or args.strategy):
        print("Nothing selected. Use --source-id, --industry, --strategy or --all.", file=sys.stderr)
        return 2

    storage_kwargs = {"base_dir": args.out} if args.storage == "local" else {}
    storage = StorageFactory.create(args.storage, **storage_kwargs)
    # An explicit non-active --status (e.g. "blocked") means: try those sources anyway
    results = run_sources(configs, storage, force=args.force, limit=args.limit,
                          run_inactive=args.status != "active")

    _print_results(results)
    if args.storage == "local":
        report = _write_report(Path(args.out), results)
        print(f"\nReport: {report}")
    return 0 if all(r.status in ("success", "skipped") for r in results) else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scraping.cli", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config-dir", help="Directory with source YAML files")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Load and validate all config files")

    def add_filters(p: argparse.ArgumentParser, default_status: str) -> None:
        p.add_argument("--source-id", action="append", help="Source id (repeatable)")
        p.add_argument("--industry")
        p.add_argument("--strategy")
        p.add_argument("--status", choices=STATUS_CHOICES, default=default_status,
                       help=f"Filter by status (default: {default_status})")

    add_filters(sub.add_parser("list", help="List configured sources"), "all")

    run = sub.add_parser("run", help="Run scrapers")
    add_filters(run, "active")
    run.add_argument("--all", action="store_true", help="Run every source matching --status")
    run.add_argument("--storage", choices=["local", "s3"], default="local")
    run.add_argument("--out", default="output", help="Output directory for local storage")
    run.add_argument("--force", action="store_true", help="Re-download even if already stored")
    run.add_argument("--limit", type=int, help="Max documents per source")
    return parser


def _statuses(value: str):
    if value == "all":
        return None
    return (SourceStatus(value),)


def _print_sources(configs) -> None:
    print(f"{'ID':<42} {'STRATEGY':<12} {'FETCH':<8} {'STATUS':<20} {'INDUSTRIES':<28} URL")
    for c in configs:
        print(f"{c.id:<42} {c.strategy:<12} {c.fetch_mode:<8} {c.status.value:<20} "
              f"{','.join(c.industries):<28} {c.url or '-'}")
    print(f"\n{len(configs)} source(s)")


def _print_results(results) -> None:
    print("\n" + "=" * 100)
    print(f"{'SOURCE':<42} {'STATUS':<9} {'SAVED':>5} {'EXIST':>5}  DETAILS")
    print("-" * 100)
    for r in results:
        details = r.errors[0] if r.errors else (r.message or "")
        print(f"{r.source_id:<42} {r.status:<9} {len(r.saved):>5} {r.skipped_existing:>5}  "
              f"{details[:120]}")
        for extra in r.errors[1:]:
            print(f"{'':<65}{extra[:120]}")
    counts = Counter(r.status for r in results)
    print("-" * 100)
    print(f"{len(results)} source(s): {dict(counts)}")


def _write_report(out_dir: Path, results) -> Path:
    report_dir = out_dir / "_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"run-{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path


if __name__ == "__main__":
    sys.exit(main())
