"""Run the Vicmap acquisition, wrangling and validation workflow."""

# 1. Imports
import argparse
import subprocess
import sys
from pathlib import Path
from time import perf_counter

# 2. Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]

ACQUISITION_SCRIPT = PROJECT_ROOT / "pipeline" / "acquisition" / "fetch_vicmap.py"
WRANGLING_SCRIPT = PROJECT_ROOT / "pipeline" / "wrangling" / "wrangle_vicmap.py"
VALIDATION_SCRIPT = PROJECT_ROOT / "pipeline" / "validation" / "validate_vicmap.py"

DEFAULT_PAGE_SIZE = 5_000


# 3. Pipeline functions
def validate_pipeline_files():
    """Confirm that every required pipeline script exists."""

    required_scripts = [
        ACQUISITION_SCRIPT,
        WRANGLING_SCRIPT,
        VALIDATION_SCRIPT,
    ]
    missing_scripts = [
        script_path for script_path in required_scripts if not script_path.exists()
    ]

    if missing_scripts:
        missing_text = ", ".join(str(path) for path in missing_scripts)
        raise FileNotFoundError(f"Required pipeline scripts not found: {missing_text}")


def run_step(step_name, command):
    """Run one pipeline step and stop immediately if it fails."""

    print(f"\n=== {step_name} ===", flush=True)
    started_at = perf_counter()

    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True,
    )

    elapsed_seconds = perf_counter() - started_at
    print(
        f"=== {step_name} completed in {elapsed_seconds:.1f} seconds ===",
        flush=True,
    )


def run_pipeline(refresh, page_size):
    """Run an optional source refresh followed by wrangling and validation."""

    validate_pipeline_files()
    pipeline_started_at = perf_counter()

    if refresh:
        run_step(
            "Vicmap acquisition",
            [
                sys.executable,
                str(ACQUISITION_SCRIPT),
                "--download",
                "--page-size",
                str(page_size),
            ],
        )
    else:
        print(
            "Using the latest existing raw Vicmap snapshot. "
            "No API download requested.",
            flush=True,
        )

    run_step(
        "Vicmap wrangling",
        [sys.executable, str(WRANGLING_SCRIPT)],
    )
    run_step(
        "Vicmap validation",
        [sys.executable, str(VALIDATION_SCRIPT)],
    )

    elapsed_seconds = perf_counter() - pipeline_started_at
    print(
        "\nVicmap pipeline completed successfully. "
        f"Total time: {elapsed_seconds:.1f} seconds.",
        flush=True,
    )


# 4. Command-line interface
def parse_arguments():
    """Parse explicit refresh and WFS pagination options."""

    parser = argparse.ArgumentParser(
        description=(
            "Run Vicmap wrangling and validation, with an optional WFS refresh."
        )
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Download a new dated WFS snapshot before processing.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=(
            "WFS records requested per page when --refresh is used "
            f"(default: {DEFAULT_PAGE_SIZE})."
        ),
    )

    arguments = parser.parse_args()

    if arguments.page_size <= 0:
        parser.error("--page-size must be a positive integer.")

    if not arguments.refresh and arguments.page_size != DEFAULT_PAGE_SIZE:
        parser.error("--page-size can only be changed together with --refresh.")

    return arguments


# 5. Script entry point
def main():
    """Run the requested Vicmap pipeline mode."""

    arguments = parse_arguments()

    try:
        run_pipeline(
            refresh=arguments.refresh,
            page_size=arguments.page_size,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        print(f"\nVicmap pipeline failed: {error}", file=sys.stderr, flush=True)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
