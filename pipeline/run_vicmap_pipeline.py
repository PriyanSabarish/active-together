"""Run the complete Vicmap data pipeline."""

import argparse
import subprocess
import sys
from pathlib import Path
from time import perf_counter


# Pipeline scripts
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FETCH_SCRIPT = PROJECT_ROOT / "pipeline" / "acquisition" / "fetch_vicmap.py"
WRANGLE_SCRIPT = PROJECT_ROOT / "pipeline" / "wrangling" / "wrangle_vicmap.py"
VALIDATE_SCRIPT = PROJECT_ROOT / "pipeline" / "validation" / "validate_vicmap.py"

DEFAULT_PAGE_SIZE = 5_000


def run_step(step_name, script_path, extra_arguments=None):
    """Run one Python script and stop if it fails."""

    if not script_path.exists():
        raise FileNotFoundError(f"Pipeline script not found: {script_path}")

    command = [sys.executable, str(script_path)]

    if extra_arguments:
        command.extend(extra_arguments)

    print(f"\n=== {step_name} ===", flush=True)
    start_time = perf_counter()

    subprocess.run(command, cwd=PROJECT_ROOT, check=True)

    elapsed = perf_counter() - start_time
    print(f"=== {step_name} completed in {elapsed:.1f} seconds ===", flush=True)


def parse_arguments():
    """Read the optional API refresh settings."""

    parser = argparse.ArgumentParser(
        description="Run Vicmap wrangling and validation."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Download a new Vicmap snapshot before processing.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"WFS records per page (default: {DEFAULT_PAGE_SIZE}).",
    )

    arguments = parser.parse_args()

    if arguments.page_size <= 0:
        parser.error("--page-size must be a positive integer.")
    if not arguments.refresh and arguments.page_size != DEFAULT_PAGE_SIZE:
        parser.error("--page-size can only be used with --refresh.")

    return arguments


def main():
    """Run acquisition when requested, then wrangling and validation."""

    arguments = parse_arguments()
    pipeline_start = perf_counter()

    try:
        if arguments.refresh:
            run_step(
                "Vicmap acquisition",
                FETCH_SCRIPT,
                ["--download", "--page-size", str(arguments.page_size)],
            )
        else:
            print(
                "Using the latest existing raw Vicmap snapshot. "
                "No API download requested.",
                flush=True,
            )

        run_step("Vicmap wrangling", WRANGLE_SCRIPT)
        run_step("Vicmap validation", VALIDATE_SCRIPT)
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        print(f"\nVicmap pipeline failed: {error}", file=sys.stderr, flush=True)
        return 1

    elapsed = perf_counter() - pipeline_start
    print(
        f"\nVicmap pipeline completed successfully in {elapsed:.1f} seconds.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
