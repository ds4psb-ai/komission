"""
run_provider_pipeline.py

Run provider CSV pull + DB ingest + Sheet sync + selector in one shot.

Usage:
  python backend/scripts/run_provider_pipeline.py --config backend/provider_sources.json
"""
import argparse
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_step(label: str, args: list[str]) -> None:
    print(f"[pipeline] {label}")
    subprocess.run(args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run provider ingest pipeline")
    parser.add_argument("--config", default=os.path.join(BASE_DIR, "provider_sources.json"))
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    python = sys.executable
    run_step("pull provider csv", [python, os.path.join(BASE_DIR, "scripts", "pull_provider_csv.py"), "--config", args.config])
    run_step("sync outliers to sheet", [python, os.path.join(BASE_DIR, "scripts", "sync_outliers_to_sheet.py"), "--limit", str(args.limit), "--status", "pending,selected"])
    run_step("run selector", [python, os.path.join(BASE_DIR, "scripts", "run_selector.py")])


if __name__ == "__main__":
    main()
