"""Run the complete Iteration 2 council name-enrichment workflow."""

import argparse
import subprocess
import sys
from pathlib import Path
from time import perf_counter

# Pipeline scripts
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = PROJECT_ROOT / "pipeline"

STEPS = [
    (
        "Monash name wrangling",
        PIPELINE_DIR / "wrangling" / "wrangle_monash_names.py",
    ),
    (
        "Monash name validation",
        PIPELINE_DIR / "validation" / "validate_monash_names.py",
    ),
    (
        "Melbourne name wrangling",
        PIPELINE_DIR / "wrangling" / "wrangle_melbourne_names.py",
    ),
    (
        "Melbourne name validation",
        PIPELINE_DIR / "validation" / "validate_melbourne_names.py",
    ),
    (
        "Melton name wrangling",
        PIPELINE_DIR / "wrangling" / "wrangle_melton_names.py",
    ),
    (
        "Melton name validation",
        PIPELINE_DIR / "validation" / "validate_melton_names.py",
    ),
    (
        "Name-enrichment consolidation",
        PIPELINE_DIR / "wrangling" / "consolidate_name_enrichment.py",
    ),
]

FINAL_VALIDATION_SCRIPT = (
    PIPELINE_DIR / "validation" / "validate_name_enrichment.py"
)


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
    """Read the optional publication setting."""

    parser = argparse.ArgumentParser(
        description="Run fixed-snapshot council name enrichment."
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish data/vicmap_app_ready.csv after all checks pass.",
    )
    return parser.parse_args()


def main():
    """Run every reviewed enrichment stage in order."""

    arguments = parse_arguments()
    pipeline_start = perf_counter()

    print(
        "Using fixed, manually reviewed council snapshots. "
        "No source download will run.",
        flush=True,
    )

    try:
        for step_name, script_path in STEPS:
            run_step(step_name, script_path)

        validation_arguments = ["--publish"] if arguments.publish else None
        final_step_name = (
            "Final validation and publication"
            if arguments.publish
            else "Final name-enrichment validation"
        )
        run_step(
            final_step_name,
            FINAL_VALIDATION_SCRIPT,
            validation_arguments,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        print(
            f"\nName-enrichment pipeline failed: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 1

    elapsed = perf_counter() - pipeline_start
    result = "validated and published" if arguments.publish else "validated"
    print(
        f"\nName-enrichment pipeline {result} successfully "
        f"in {elapsed:.1f} seconds.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
