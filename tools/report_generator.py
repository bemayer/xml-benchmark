#!/usr/bin/env python3
"""Read benchmark results and inject into HTML report template."""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from common import LIBRARIES, OPERATIONS, OPERATION_LABELS, SIZES, RESULTS_DIR, REPORT_TEMPLATE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_results() -> list[dict]:
    results = []
    path = os.path.join(ROOT, RESULTS_DIR, "results.jsonl")
    if not os.path.exists(path):
        print(f"No results file at {path}")
        return results
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                if not data.get("skipped"):
                    results.append(data)
    return results


def size_label_from_filename(filename: str) -> str:
    for s in SIZES:
        if s in filename:
            return s
    return "other"


def build_benchmark_data(results: list[dict]) -> dict:
    # First pass: collect all entries per (op, size, library)
    raw = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in results:
        op_label = OPERATION_LABELS.get(r["operation"], r["operation"])
        fname = os.path.basename(r.get("file", ""))
        size_label = size_label_from_filename(fname)
        raw[op_label][size_label][r["library"]].append({
            "time_ms": r.get("time_ms", 0),
            "throughput_mbs": r.get("throughput_mbs", 0),
            "memory_mb": r.get("peak_rss_mb", 0),
            "cpu_ms": round(r.get("cpu_user_ms", 0) + r.get("cpu_system_ms", 0), 3),
        })

    # Second pass: average across shapes (wide/deep/realworld) per library
    grouped = defaultdict(lambda: defaultdict(list))
    for op in raw:
        for size in raw[op]:
            for lib, entries in raw[op][size].items():
                n = len(entries)
                grouped[op][size].append({
                    "library": lib,
                    "time_ms": round(sum(e["time_ms"] for e in entries) / n, 3),
                    "throughput_mbs": round(sum(e["throughput_mbs"] for e in entries) / n, 1),
                    "memory_mb": round(sum(e["memory_mb"] for e in entries) / n, 1),
                    "cpu_ms": round(sum(e["cpu_ms"] for e in entries) / n, 3),
                })

    for op in grouped:
        for size in grouped[op]:
            grouped[op][size].sort(key=lambda x: x["time_ms"])

    return {
        "meta": {
            "date": datetime.now(timezone.utc).isoformat(),
            "runner": os.environ.get("RUNNER_INFO", "local"),
            "lib_count": len(LIBRARIES),
            "op_count": len(OPERATIONS),
        },
        "sizes": SIZES,
        "operations": list(OPERATION_LABELS.values()),
        "libraries": [
            {"name": l["name"], "lang": l["lang"], "langClass": l["lang_class"]}
            for l in LIBRARIES
        ],
        "results": {op: dict(sizes) for op, sizes in grouped.items()},
    }


def inject_into_template(data: dict) -> str:
    template_path = os.path.join(ROOT, REPORT_TEMPLATE)
    with open(template_path) as f:
        html = f.read()

    data_json = json.dumps(data, indent=2)

    pattern = r"const BENCHMARK_DATA = \{[\s\S]*?generateSampleData\(\)[\s\S]*?\};"
    replacement = f"const BENCHMARK_DATA = {data_json};"
    html = re.sub(pattern, replacement, html)

    pattern2 = r"function generateSampleData\(\) \{[\s\S]*?\n\}"
    html = re.sub(pattern2, "", html)

    return html


def main():
    results = load_results()
    if not results:
        print("No results to report.")
        return

    print(f"Loaded {len(results)} result entries.")
    data = build_benchmark_data(results)

    html = inject_into_template(data)

    output_path = os.path.join(ROOT, "report", "index.html")
    with open(output_path, "w") as f:
        f.write(html)
    print(f"Report written to {output_path}")


if __name__ == "__main__":
    main()
