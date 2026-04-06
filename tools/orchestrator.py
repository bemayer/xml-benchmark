#!/usr/bin/env python3
"""Build Docker images and run all benchmarks sequentially."""

import json
import os
import subprocess
import sys
import glob
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))
from common import LIBRARIES, OPERATIONS, SIZES, SHAPES, DATA_DIR, RESULTS_DIR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARKS_DIR = os.path.join(ROOT, "benchmarks")


def build_image(lib: dict) -> str:
    tag = f"xmlbench-{lib['dir']}"
    bench_dir = os.path.join(BENCHMARKS_DIR, lib["dir"])
    runner_src = os.path.join(BENCHMARKS_DIR, "runner.sh")
    runner_dst = os.path.join(bench_dir, "runner.sh")
    shutil.copy2(runner_src, runner_dst)
    print(f"  building {tag}...")
    subprocess.run(
        ["docker", "build", "-t", tag, "."],
        cwd=bench_dir,
        check=True,
        capture_output=True,
    )
    os.remove(runner_dst)
    return tag


def build_all_images():
    print("Building Docker images...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(build_image, lib): lib for lib in LIBRARIES}
        for future in as_completed(futures):
            lib = futures[future]
            try:
                tag = future.result()
                print(f"    {tag} OK")
            except Exception as e:
                print(f"    FAIL {lib['dir']}: {e}")


def auto_iterations(file_size_bytes: int) -> int:
    if file_size_bytes > 50_000_000: return 1
    elif file_size_bytes > 5_000_000: return 5
    elif file_size_bytes > 500_000: return 20
    elif file_size_bytes > 50_000: return 100
    else: return 500


def run_benchmark(lib: dict, operation: str, data_file: str, iterations: int):
    tag = f"xmlbench-{lib['dir']}"
    data_abs = os.path.abspath(DATA_DIR)
    results_abs = os.path.abspath(RESULTS_DIR)
    container_data = "/data"
    container_results = "/results"
    container_file = f"{container_data}/{os.path.basename(data_file)}"

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{data_abs}:{container_data}:ro",
            "-v", f"{results_abs}:{container_results}",
            tag,
            operation, container_file, str(iterations), container_results,
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        print(f"      WARN: {lib['name']} {operation} failed: {result.stderr[:200]}")


def collect_data_files() -> list[str]:
    return sorted(glob.glob(os.path.join(DATA_DIR, "*.xml")))


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    results_file = os.path.join(RESULTS_DIR, "results.jsonl")
    if os.path.exists(results_file):
        os.remove(results_file)

    print("Ensuring test data exists...")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "generate_data.py")], check=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "download_data.py")], check=True)

    build_all_images()

    data_files = collect_data_files()
    print(f"\nRunning benchmarks ({len(LIBRARIES)} libraries x {len(OPERATIONS)} ops x {len(data_files)} files)...")

    for lib in LIBRARIES:
        for operation in OPERATIONS:
            if operation not in lib["ops"]:
                continue
            for data_file in data_files:
                file_size = os.path.getsize(data_file)
                iterations = auto_iterations(file_size)
                fname = os.path.basename(data_file)
                print(f"  {lib['name']:20s} {operation:15s} {fname:25s} x{iterations}")
                run_benchmark(lib, operation, data_file, iterations)

    print(f"\nResults written to {results_file}")
    print("Generating report...")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "report_generator.py")], check=True)
    print("Done.")


if __name__ == "__main__":
    main()
