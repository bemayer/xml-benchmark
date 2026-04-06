#!/usr/bin/env python3
"""Read benchmark results and inject into HTML report template."""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from common import LIBRARIES, OPERATIONS, OPERATION_LABELS, SIZES, SIZE_BYTES, RESULTS_DIR, REPORT_TEMPLATE

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
            "file_size_bytes": r.get("file_size_bytes", 0),
            "memory_mb": r.get("peak_rss_mb", 0),
            "cpu_ms": round(r.get("cpu_user_ms", 0) + r.get("cpu_system_ms", 0), 3),
        })

    # Second pass: average across shapes (wide/deep/realworld) per library
    # Throughput is recalculated from averaged time + averaged file size (not averaged directly)
    grouped = defaultdict(lambda: defaultdict(list))
    for op in raw:
        for size in raw[op]:
            for lib, entries in raw[op][size].items():
                n = len(entries)
                avg_time = sum(e["time_ms"] for e in entries) / n
                avg_file_bytes = sum(e["file_size_bytes"] for e in entries) / n
                throughput = round(avg_file_bytes / 1048576 / (avg_time / 1000), 1) if avg_time > 0 else 0
                grouped[op][size].append({
                    "library": lib,
                    "time_ms": round(avg_time, 3),
                    "throughput_mbs": throughput,
                    "memory_mb": round(sum(e["memory_mb"] for e in entries) / n, 1),
                    "cpu_ms": round(sum(e["cpu_ms"] for e in entries) / n, 3),
                })

    for op in grouped:
        for size in grouped[op]:
            grouped[op][size].sort(key=lambda x: x["time_ms"])

    # Compute aggregate scores per library
    # Methodology:
    #   - For each (operation, size) cell, compute relative speed: best_time / lib_time
    #     (1.0 = fastest, 0.5 = twice as slow, etc.)
    #   - Weight by file size: log2(bytes) so 10MB counts ~13x more than 1KB
    #   - Weight by operation universality: dom_parse 3x, sax_parse 2x, xpath 1.5x, serialize 1x
    #   - A library only scores on operations it supports (no penalty for missing ops)
    #   - Final score = weighted average of relative speeds (0-100 scale)
    import math
    OP_WEIGHT = {"DOM Parse": 3.0, "SAX/Stream": 2.0, "XPath Query": 1.5, "Serialize": 1.0}
    lib_scores = defaultdict(lambda: {"weighted_sum": 0.0, "weight_total": 0.0})
    for op in grouped:
        op_w = OP_WEIGHT.get(op, 1.0)
        for size in grouped[op]:
            size_bytes = SIZE_BYTES.get(size, 1048576)
            size_w = math.log2(max(size_bytes, 1))
            entries = grouped[op][size]
            if not entries:
                continue
            best_time = min(e["time_ms"] for e in entries)
            if best_time <= 0:
                continue
            for e in entries:
                if e["time_ms"] <= 0:
                    continue
                relative = best_time / e["time_ms"]  # 1.0 = best
                w = op_w * size_w
                lib_scores[e["library"]]["weighted_sum"] += relative * w
                lib_scores[e["library"]]["weight_total"] += w

    rankings = []
    for lib_name, s in lib_scores.items():
        if s["weight_total"] > 0:
            score = round(s["weighted_sum"] / s["weight_total"] * 100, 1)
        else:
            score = 0
        rankings.append({"library": lib_name, "score": score})
    rankings.sort(key=lambda x: x["score"], reverse=True)

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
        "rankings": rankings,
    }


def inject_into_template(data: dict) -> str:
    template_path = os.path.join(ROOT, REPORT_TEMPLATE)
    with open(template_path) as f:
        html = f.read()

    data_json = json.dumps(data, indent=2)

    # Replace BENCHMARK_DATA assignment — works whether it contains sample or real data
    # Match from "const BENCHMARK_DATA =" to the next top-level "// ===" comment block
    pattern = r"const BENCHMARK_DATA = [\s\S]*?;\n\nfunction generateSampleData[\s\S]*?\n\}\n"
    replacement = f"const BENCHMARK_DATA = {data_json};\n"
    new_html = re.sub(pattern, replacement, html, count=1)
    if new_html == html:
        # Already has real data injected — replace the existing data object
        pattern2 = r"const BENCHMARK_DATA = \{[\s\S]*?\n\};\n"
        replacement2 = f"const BENCHMARK_DATA = {data_json};\n"
        new_html = re.sub(pattern2, replacement2, html, count=1)
    return new_html

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
