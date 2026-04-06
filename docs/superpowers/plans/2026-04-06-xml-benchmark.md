# XML Benchmark Suite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-language XML benchmark suite that compares 14 libraries across 7 languages, runs in Docker, and publishes results as a static HTML report to GitHub Pages monthly.

**Architecture:** Each library gets its own Docker container with a benchmark binary/script that outputs JSON results. A Python orchestrator builds images, runs containers sequentially, collects results, and a report generator injects them into an existing HTML template. GitHub Actions runs this monthly.

**Tech Stack:** Python 3.12 (orchestrator/tools), Docker (isolation), C++ (CMake), Rust (Cargo), Java (Maven), Go, C# (.NET 8), Node.js, Chart.js (report)

---

## File Structure

```
xml-benchmark/
├── .github/workflows/benchmark.yml
├── .gitignore
├── tools/
│   ├── generate_data.py          # Synthetic XML generator
│   ├── download_data.py          # Real-world XML downloader
│   ├── orchestrator.py           # Build & run all benchmarks
│   ├── report_generator.py       # JSON results -> HTML report
│   └── common.py                 # Shared constants (sizes, operations, library metadata)
├── benchmarks/
│   ├── runner.sh                 # Shared entrypoint wrapper (measures RSS/CPU via /usr/bin/time)
│   ├── pugixml/
│   │   ├── Dockerfile
│   │   ├── CMakeLists.txt
│   │   └── bench.cpp
│   ├── rapidxml/
│   │   ├── Dockerfile
│   │   ├── CMakeLists.txt
│   │   └── bench.cpp
│   ├── expat/
│   │   ├── Dockerfile
│   │   ├── CMakeLists.txt
│   │   └── bench.cpp
│   ├── libxml2/
│   │   ├── Dockerfile
│   │   ├── CMakeLists.txt
│   │   └── bench.cpp
│   ├── vtd-xml/
│   │   ├── Dockerfile
│   │   ├── pom.xml
│   │   └── src/main/java/bench/Bench.java
│   ├── xerces/
│   │   ├── Dockerfile
│   │   ├── pom.xml
│   │   └── src/main/java/bench/Bench.java
│   ├── woodstox/
│   │   ├── Dockerfile
│   │   ├── pom.xml
│   │   └── src/main/java/bench/Bench.java
│   ├── lxml/
│   │   ├── Dockerfile
│   │   └── bench.py
│   ├── celementtree/
│   │   ├── Dockerfile
│   │   └── bench.py
│   ├── quick-xml/
│   │   ├── Dockerfile
│   │   ├── Cargo.toml
│   │   └── src/main.rs
│   ├── roxmltree/
│   │   ├── Dockerfile
│   │   ├── Cargo.toml
│   │   └── src/main.rs
│   ├── system-xml/
│   │   ├── Dockerfile
│   │   ├── SystemXmlBench.csproj
│   │   └── Program.cs
│   ├── encoding-xml/
│   │   ├── Dockerfile
│   │   ├── go.mod
│   │   └── main.go
│   └── fast-xml-parser/
│       ├── Dockerfile
│       ├── package.json
│       └── bench.js
├── report/
│   └── index.html                # Already built — template with sample data
├── data/                         # Generated at runtime, gitignored
└── results/                      # JSON output, gitignored
```

## JSON Output Contract

Every benchmark binary outputs one JSON object per operation to stdout. The shared `runner.sh` wrapper captures timing/memory and merges it. Final JSON per run:

```json
{
  "library": "pugixml",
  "language": "C++",
  "operation": "dom_parse",
  "file": "wide_10MB.xml",
  "file_size_bytes": 10485760,
  "iterations": 50,
  "time_ms": 12.345,
  "throughput_mbs": 810.5,
  "peak_rss_mb": 45.2,
  "cpu_user_ms": 10.1,
  "cpu_system_ms": 2.2
}
```

Each benchmark binary receives these arguments:
```
./bench <operation> <input_file> <iterations>
```

Operations: `dom_parse`, `sax_parse`, `xpath_query`, `serialize`

The binary prints one line of JSON per invocation. It must handle "not supported" by printing `{"skipped": true, "operation": "xpath_query", "library": "RapidXML"}`.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `.gitignore`
- Create: `tools/common.py`

- [ ] **Step 1: Initialize git repo**

```bash
cd /c/Users/mayer/Documents/xml-benchmark
git init
```

- [ ] **Step 2: Create .gitignore**

```gitignore
data/
results/
__pycache__/
*.pyc
.venv/
node_modules/
target/
bin/
obj/
```

- [ ] **Step 3: Create tools/common.py with shared constants**

```python
"""Shared constants for the XML benchmark suite."""

SIZES = ["1KB", "100KB", "1MB", "10MB", "100MB"]

SIZE_BYTES = {
    "1KB": 1024,
    "100KB": 102_400,
    "1MB": 1_048_576,
    "10MB": 10_485_760,
    "100MB": 104_857_600,
}

OPERATIONS = ["dom_parse", "sax_parse", "xpath_query", "serialize"]

OPERATION_LABELS = {
    "dom_parse": "DOM Parse",
    "sax_parse": "SAX/Stream",
    "xpath_query": "XPath Query",
    "serialize": "Serialize",
}

LIBRARIES = [
    {"name": "pugixml",         "dir": "pugixml",         "lang": "C++",    "lang_class": "cpp",    "ops": ["dom_parse", "xpath_query", "serialize"]},
    {"name": "RapidXML",        "dir": "rapidxml",        "lang": "C++",    "lang_class": "cpp",    "ops": ["dom_parse", "serialize"]},
    {"name": "Expat",           "dir": "expat",           "lang": "C++",    "lang_class": "cpp",    "ops": ["sax_parse"]},
    {"name": "libxml2",         "dir": "libxml2",         "lang": "C++",    "lang_class": "cpp",    "ops": ["dom_parse", "sax_parse", "xpath_query", "serialize"]},
    {"name": "VTD-XML",         "dir": "vtd-xml",         "lang": "Java",   "lang_class": "java",   "ops": ["dom_parse", "xpath_query"]},
    {"name": "Xerces",          "dir": "xerces",          "lang": "Java",   "lang_class": "java",   "ops": ["dom_parse", "sax_parse", "xpath_query", "serialize"]},
    {"name": "Woodstox",        "dir": "woodstox",        "lang": "Java",   "lang_class": "java",   "ops": ["sax_parse"]},
    {"name": "lxml",            "dir": "lxml",            "lang": "Python", "lang_class": "python", "ops": ["dom_parse", "xpath_query", "serialize"]},
    {"name": "cElementTree",    "dir": "celementtree",    "lang": "Python", "lang_class": "python", "ops": ["dom_parse", "serialize"]},
    {"name": "quick-xml",       "dir": "quick-xml",       "lang": "Rust",   "lang_class": "rust",   "ops": ["dom_parse", "sax_parse", "serialize"]},
    {"name": "roxmltree",       "dir": "roxmltree",       "lang": "Rust",   "lang_class": "rust",   "ops": ["dom_parse"]},
    {"name": "System.Xml",      "dir": "system-xml",      "lang": "C#",     "lang_class": "csharp", "ops": ["dom_parse", "sax_parse", "xpath_query", "serialize"]},
    {"name": "encoding/xml",    "dir": "encoding-xml",    "lang": "Go",     "lang_class": "go",     "ops": ["dom_parse", "sax_parse", "serialize"]},
    {"name": "fast-xml-parser", "dir": "fast-xml-parser", "lang": "JS",     "lang_class": "js",     "ops": ["dom_parse", "serialize"]},
]

SHAPES = ["wide", "deep"]

DATA_DIR = "data"
RESULTS_DIR = "results"
REPORT_TEMPLATE = "report/index.html"
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore tools/common.py
git commit -m "chore: project scaffolding with shared constants"
```

---

### Task 2: Synthetic XML Data Generator

**Files:**
- Create: `tools/generate_data.py`

- [ ] **Step 1: Create generate_data.py**

```python
#!/usr/bin/env python3
"""Generate synthetic XML test files at various sizes and shapes."""

import os
import sys
import math

sys.path.insert(0, os.path.dirname(__file__))
from common import SIZE_BYTES, SHAPES, DATA_DIR


def generate_wide(target_bytes: int) -> str:
    """Many sibling elements, 2 levels deep."""
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n'
    footer = "</root>\n"
    item_template = '  <item id="{i}" name="element_{i}" value="{val}" active="true" score="{score}">\n    <desc>Description text for item number {i} with some padding content here</desc>\n  </item>\n'
    overhead = len(header.encode()) + len(footer.encode())
    sample_item = item_template.format(i=0, val="sample_value_0", score="0.00")
    item_size = len(sample_item.encode())
    count = max(1, (target_bytes - overhead) // item_size)
    parts = [header]
    for i in range(count):
        parts.append(item_template.format(i=i, val=f"value_{i}", score=f"{i * 0.01:.2f}"))
    parts.append(footer)
    return "".join(parts)


def generate_deep(target_bytes: int) -> str:
    """Deeply nested elements, few siblings per level."""
    overhead_per_level = 60  # rough estimate for open+close tags + attrs
    depth = max(1, target_bytes // overhead_per_level)
    # Cap depth to avoid stack issues, fill remaining with text content
    depth = min(depth, 5000)
    parts = ['<?xml version="1.0" encoding="UTF-8"?>\n']
    for i in range(depth):
        indent = "  " * i
        parts.append(f'{indent}<level id="{i}" depth="{i}">\n')
    # Add leaf content to reach target size
    current_size = sum(len(p.encode()) for p in parts)
    close_size = sum(len(("  " * i + "</level>\n").encode()) for i in range(depth - 1, -1, -1))
    remaining = target_bytes - current_size - close_size
    if remaining > 0:
        indent = "  " * depth
        # Fill with text content
        filler_line = indent + "<data>Lorem ipsum dolor sit amet padding</data>\n"
        filler_size = len(filler_line.encode())
        filler_count = max(1, remaining // filler_size)
        for _ in range(filler_count):
            parts.append(filler_line)
    for i in range(depth - 1, -1, -1):
        indent = "  " * i
        parts.append(f"{indent}</level>\n")
    return "".join(parts)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    generators = {"wide": generate_wide, "deep": generate_deep}
    for size_label, size_bytes in SIZE_BYTES.items():
        for shape in SHAPES:
            filename = f"{shape}_{size_label}.xml"
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.exists(filepath):
                print(f"  skip {filename} (exists)")
                continue
            print(f"  generating {filename} (~{size_label})...")
            xml = generators[shape](size_bytes)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(xml)
            actual = os.path.getsize(filepath)
            print(f"    -> {actual:,} bytes")
    print("Done.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the generator**

```bash
cd /c/Users/mayer/Documents/xml-benchmark
python tools/generate_data.py
ls -la data/
```

Expected: 10 XML files (5 sizes x 2 shapes), sizes approximately matching targets.

- [ ] **Step 3: Commit**

```bash
git add tools/generate_data.py
git commit -m "feat: synthetic XML data generator (wide/deep shapes, 1KB-100MB)"
```

---

### Task 3: Real-World Data Downloader

**Files:**
- Create: `tools/download_data.py`

- [ ] **Step 1: Create download_data.py**

```python
#!/usr/bin/env python3
"""Download real-world XML test files."""

import os
import sys
import urllib.request
import gzip
import shutil

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA_DIR

# Public XML datasets — small extracts
DATASETS = [
    {
        "name": "dblp_10MB",
        "url": "https://dblp.org/xml/release/dblp-2024-01-01.xml.gz",
        "filename": "realworld_dblp.xml",
        "max_bytes": 10 * 1024 * 1024,  # truncate to ~10MB
        "compressed": True,
    },
    {
        "name": "osm_10MB",
        "url": "https://overpass-api.de/api/map?bbox=2.33,48.85,2.36,48.87",
        "filename": "realworld_osm.xml",
        "max_bytes": 10 * 1024 * 1024,
        "compressed": False,
    },
]


def download_and_truncate(dataset: dict) -> None:
    filepath = os.path.join(DATA_DIR, dataset["filename"])
    if os.path.exists(filepath):
        print(f"  skip {dataset['filename']} (exists)")
        return

    print(f"  downloading {dataset['name']}...")
    tmp_path = filepath + ".tmp"
    try:
        req = urllib.request.Request(dataset["url"], headers={"User-Agent": "xml-benchmark/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(tmp_path, "wb") as f:
                if dataset.get("compressed"):
                    # Download full gzip, decompress, truncate
                    raw = resp.read()
                    decompressed = gzip.decompress(raw)
                    # Truncate at last complete tag before max_bytes
                    chunk = decompressed[: dataset["max_bytes"]]
                    # Find last closing tag
                    last_close = chunk.rfind(b"</")
                    if last_close > 0:
                        end = chunk.find(b">", last_close)
                        if end > 0:
                            chunk = chunk[: end + 1]
                    # Ensure we close the root
                    chunk += b"\n</dblp>\n"
                    f.write(chunk)
                else:
                    written = 0
                    while written < dataset["max_bytes"]:
                        block = resp.read(65536)
                        if not block:
                            break
                        f.write(block)
                        written += len(block)
        shutil.move(tmp_path, filepath)
        actual = os.path.getsize(filepath)
        print(f"    -> {actual:,} bytes")
    except Exception as e:
        print(f"    WARN: failed to download {dataset['name']}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    for ds in DATASETS:
        download_and_truncate(ds)
    print("Done.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the downloader** (network required)

```bash
python tools/download_data.py
ls -la data/realworld_*
```

- [ ] **Step 3: Commit**

```bash
git add tools/download_data.py
git commit -m "feat: real-world XML data downloader (DBLP, OSM)"
```

---

### Task 4: Shared Benchmark Runner Script

**Files:**
- Create: `benchmarks/runner.sh`

This wrapper runs any benchmark binary, captures wall time, peak RSS, and CPU time via `/usr/bin/time -v`, then merges the metrics into the benchmark's JSON output.

- [ ] **Step 1: Create runner.sh**

```bash
#!/usr/bin/env bash
# runner.sh — wraps a benchmark binary, captures system metrics, enriches JSON output
# Usage: runner.sh <benchmark_cmd> <operation> <input_file> <iterations> <output_dir>
set -euo pipefail

BENCH_CMD="$1"
OPERATION="$2"
INPUT_FILE="$3"
ITERATIONS="$4"
OUTPUT_DIR="$5"

LIBRARY_NAME=$(basename "$(dirname "$BENCH_CMD")" 2>/dev/null || basename "$BENCH_CMD")

# Use GNU time to capture memory/CPU
TIME_OUTPUT=$(mktemp)
BENCH_OUTPUT=$(mktemp)

/usr/bin/time -v -o "$TIME_OUTPUT" \
  "$BENCH_CMD" "$OPERATION" "$INPUT_FILE" "$ITERATIONS" > "$BENCH_OUTPUT" 2>/dev/null || true

# Parse /usr/bin/time output
WALL_SEC=$(grep "Elapsed (wall clock)" "$TIME_OUTPUT" | sed -E 's/.*: (.*)/\1/')
RSS_KB=$(grep "Maximum resident set size" "$TIME_OUTPUT" | awk '{print $NF}')
USER_SEC=$(grep "User time" "$TIME_OUTPUT" | awk '{print $NF}')
SYS_SEC=$(grep "System time" "$TIME_OUTPUT" | awk '{print $NF}')

# Convert to ms
RSS_MB=$(echo "scale=1; $RSS_KB / 1024" | bc)
USER_MS=$(echo "scale=3; $USER_SEC * 1000" | bc)
SYS_MS=$(echo "scale=3; $SYS_SEC * 1000" | bc)
FILE_SIZE=$(stat -c%s "$INPUT_FILE" 2>/dev/null || stat -f%z "$INPUT_FILE")

# Read the benchmark's JSON output line and enrich it
if [ -s "$BENCH_OUTPUT" ]; then
  # The benchmark outputs JSON with library, operation, time_ms, iterations
  # We add peak_rss_mb, cpu_user_ms, cpu_system_ms, file_size_bytes, throughput_mbs
  python3 -c "
import json, sys
for line in open('$BENCH_OUTPUT'):
    line = line.strip()
    if not line or not line.startswith('{'):
        continue
    data = json.loads(line)
    if data.get('skipped'):
        print(json.dumps(data))
        continue
    data['peak_rss_mb'] = $RSS_MB
    data['cpu_user_ms'] = $USER_MS
    data['cpu_system_ms'] = $SYS_MS
    data['file_size_bytes'] = $FILE_SIZE
    time_s = data.get('time_ms', 0) / 1000
    if time_s > 0:
        data['throughput_mbs'] = round($FILE_SIZE / 1048576 / time_s, 1)
    print(json.dumps(data))
" >> "$OUTPUT_DIR/results.jsonl"
fi

rm -f "$TIME_OUTPUT" "$BENCH_OUTPUT"
```

- [ ] **Step 2: Commit**

```bash
chmod +x benchmarks/runner.sh
git add benchmarks/runner.sh
git commit -m "feat: shared benchmark runner with system metrics capture"
```

---

### Task 5: C++ Benchmarks (pugixml, RapidXML, Expat, libxml2)

**Files:**
- Create: `benchmarks/pugixml/bench.cpp`, `benchmarks/pugixml/CMakeLists.txt`, `benchmarks/pugixml/Dockerfile`
- Create: `benchmarks/rapidxml/bench.cpp`, `benchmarks/rapidxml/CMakeLists.txt`, `benchmarks/rapidxml/Dockerfile`
- Create: `benchmarks/expat/bench.cpp`, `benchmarks/expat/CMakeLists.txt`, `benchmarks/expat/Dockerfile`
- Create: `benchmarks/libxml2/bench.cpp`, `benchmarks/libxml2/CMakeLists.txt`, `benchmarks/libxml2/Dockerfile`

- [ ] **Step 1: Create pugixml benchmark**

`benchmarks/pugixml/bench.cpp`:
```cpp
#include <pugixml.hpp>
#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>
#include <string>
#include <cstdio>

using Clock = std::chrono::high_resolution_clock;

std::string read_file(const char* path) {
    std::ifstream f(path);
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

double bench_dom_parse(const std::string& xml, int iterations) {
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        pugi::xml_document doc;
        doc.load_string(xml.c_str());
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_xpath_query(const std::string& xml, int iterations) {
    pugi::xml_document doc;
    doc.load_string(xml.c_str());
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        pugi::xpath_query q("//*[@id]");
        auto nodes = doc.select_nodes(q);
        // Force evaluation
        volatile size_t count = std::distance(nodes.begin(), nodes.end());
        (void)count;
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_serialize(const std::string& xml, int iterations) {
    pugi::xml_document doc;
    doc.load_string(xml.c_str());
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        std::ostringstream ss;
        doc.save(ss);
        volatile size_t len = ss.str().size();
        (void)len;
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: bench <operation> <file> <iterations>\n";
        return 1;
    }
    std::string op = argv[1];
    std::string xml = read_file(argv[2]);
    int iterations = std::stoi(argv[3]);

    if (op == "dom_parse") {
        double ms = bench_dom_parse(xml, iterations);
        printf("{\"library\":\"pugixml\",\"language\":\"C++\",\"operation\":\"dom_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", argv[2], iterations, ms);
    } else if (op == "xpath_query") {
        double ms = bench_xpath_query(xml, iterations);
        printf("{\"library\":\"pugixml\",\"language\":\"C++\",\"operation\":\"xpath_query\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", argv[2], iterations, ms);
    } else if (op == "serialize") {
        double ms = bench_serialize(xml, iterations);
        printf("{\"library\":\"pugixml\",\"language\":\"C++\",\"operation\":\"serialize\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", argv[2], iterations, ms);
    } else {
        printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"pugixml\"}\n", op.c_str());
    }
    return 0;
}
```

`benchmarks/pugixml/CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.16)
project(pugixml_bench)
set(CMAKE_CXX_STANDARD 17)

include(FetchContent)
FetchContent_Declare(pugixml GIT_REPOSITORY https://github.com/zeux/pugixml.git GIT_TAG v1.14)
FetchContent_MakeAvailable(pugixml)

add_executable(bench bench.cpp)
target_link_libraries(bench pugixml::pugixml)
```

`benchmarks/pugixml/Dockerfile`:
```dockerfile
FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY CMakeLists.txt bench.cpp ./
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bench /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 2: Create RapidXML benchmark**

`benchmarks/rapidxml/bench.cpp`:
```cpp
#include "rapidxml.hpp"
#include "rapidxml_print.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>
#include <string>
#include <cstdio>
#include <vector>

using Clock = std::chrono::high_resolution_clock;

std::string read_file(const char* path) {
    std::ifstream f(path);
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

double bench_dom_parse(const std::string& xml, int iterations) {
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        std::vector<char> buf(xml.begin(), xml.end());
        buf.push_back('\0');
        rapidxml::xml_document<> doc;
        doc.parse<0>(buf.data());
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_serialize(const std::string& xml, int iterations) {
    std::vector<char> buf(xml.begin(), xml.end());
    buf.push_back('\0');
    rapidxml::xml_document<> doc;
    doc.parse<0>(buf.data());
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        std::string out;
        rapidxml::print(std::back_inserter(out), doc);
        volatile size_t len = out.size();
        (void)len;
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

int main(int argc, char* argv[]) {
    if (argc < 4) return 1;
    std::string op = argv[1];
    std::string xml = read_file(argv[2]);
    int iterations = std::stoi(argv[3]);

    if (op == "dom_parse") {
        double ms = bench_dom_parse(xml, iterations);
        printf("{\"library\":\"RapidXML\",\"language\":\"C++\",\"operation\":\"dom_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", argv[2], iterations, ms);
    } else if (op == "serialize") {
        double ms = bench_serialize(xml, iterations);
        printf("{\"library\":\"RapidXML\",\"language\":\"C++\",\"operation\":\"serialize\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", argv[2], iterations, ms);
    } else {
        printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"RapidXML\"}\n", op.c_str());
    }
    return 0;
}
```

`benchmarks/rapidxml/CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.16)
project(rapidxml_bench)
set(CMAKE_CXX_STANDARD 17)

include(FetchContent)
FetchContent_Declare(rapidxml URL https://sourceforge.net/projects/rapidxml/files/rapidxml/rapidxml%201.13/rapidxml-1.13.zip)
FetchContent_MakeAvailable(rapidxml)

add_executable(bench bench.cpp)
target_include_directories(bench PRIVATE ${rapidxml_SOURCE_DIR})
```

`benchmarks/rapidxml/Dockerfile`:
```dockerfile
FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake wget unzip ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY CMakeLists.txt bench.cpp ./
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bench /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 3: Create Expat benchmark**

`benchmarks/expat/bench.cpp`:
```cpp
#include <expat.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>
#include <string>
#include <cstdio>

using Clock = std::chrono::high_resolution_clock;

std::string read_file(const char* path) {
    std::ifstream f(path);
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

static void start_element(void*, const XML_Char*, const XML_Char**) {}
static void end_element(void*, const XML_Char*) {}
static void char_data(void*, const XML_Char*, int) {}

double bench_sax_parse(const std::string& xml, int iterations) {
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        XML_Parser parser = XML_ParserCreate(nullptr);
        XML_SetElementHandler(parser, start_element, end_element);
        XML_SetCharacterDataHandler(parser, char_data);
        XML_Parse(parser, xml.c_str(), xml.size(), XML_TRUE);
        XML_ParserFree(parser);
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

int main(int argc, char* argv[]) {
    if (argc < 4) return 1;
    std::string op = argv[1];
    std::string xml = read_file(argv[2]);
    int iterations = std::stoi(argv[3]);

    if (op == "sax_parse") {
        double ms = bench_sax_parse(xml, iterations);
        printf("{\"library\":\"Expat\",\"language\":\"C++\",\"operation\":\"sax_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", argv[2], iterations, ms);
    } else {
        printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"Expat\"}\n", op.c_str());
    }
    return 0;
}
```

`benchmarks/expat/CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.16)
project(expat_bench)
set(CMAKE_CXX_STANDARD 17)
find_package(EXPAT REQUIRED)
add_executable(bench bench.cpp)
target_link_libraries(bench EXPAT::EXPAT)
```

`benchmarks/expat/Dockerfile`:
```dockerfile
FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake libexpat1-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY CMakeLists.txt bench.cpp ./
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bench /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 4: Create libxml2 benchmark**

`benchmarks/libxml2/bench.cpp`:
```cpp
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/xpath.h>
#include <libxml/xmlsave.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>
#include <string>
#include <cstdio>

using Clock = std::chrono::high_resolution_clock;

std::string read_file(const char* path) {
    std::ifstream f(path);
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

static void sax_start(void*, const xmlChar*, const xmlChar**) {}
static void sax_end(void*, const xmlChar*) {}
static void sax_chars(void*, const xmlChar*, int) {}

double bench_dom_parse(const std::string& xml, int iterations) {
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        xmlDocPtr doc = xmlParseMemory(xml.c_str(), xml.size());
        xmlFreeDoc(doc);
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_sax_parse(const std::string& xml, int iterations) {
    xmlSAXHandler handler = {};
    handler.startElement = sax_start;
    handler.endElement = sax_end;
    handler.characters = sax_chars;
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        xmlSAXUserParseMemory(&handler, nullptr, xml.c_str(), xml.size());
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_xpath_query(const std::string& xml, int iterations) {
    xmlDocPtr doc = xmlParseMemory(xml.c_str(), xml.size());
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        xmlXPathContextPtr ctx = xmlXPathNewContext(doc);
        xmlXPathObjectPtr result = xmlXPathEvalExpression((const xmlChar*)"//*[@id]", ctx);
        volatile int count = result ? result->nodesetval->nodeNr : 0;
        (void)count;
        xmlXPathFreeObject(result);
        xmlXPathFreeContext(ctx);
    }
    auto end = Clock::now();
    xmlFreeDoc(doc);
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_serialize(const std::string& xml, int iterations) {
    xmlDocPtr doc = xmlParseMemory(xml.c_str(), xml.size());
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        xmlChar* buf = nullptr;
        int size = 0;
        xmlDocDumpMemory(doc, &buf, &size);
        volatile int len = size;
        (void)len;
        xmlFree(buf);
    }
    auto end = Clock::now();
    xmlFreeDoc(doc);
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

int main(int argc, char* argv[]) {
    if (argc < 4) return 1;
    std::string op = argv[1];
    std::string xml = read_file(argv[2]);
    int iterations = std::stoi(argv[3]);
    xmlInitParser();

    double ms = 0;
    bool skipped = false;
    if (op == "dom_parse") ms = bench_dom_parse(xml, iterations);
    else if (op == "sax_parse") ms = bench_sax_parse(xml, iterations);
    else if (op == "xpath_query") ms = bench_xpath_query(xml, iterations);
    else if (op == "serialize") ms = bench_serialize(xml, iterations);
    else skipped = true;

    if (skipped)
        printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"libxml2\"}\n", op.c_str());
    else
        printf("{\"library\":\"libxml2\",\"language\":\"C++\",\"operation\":\"%s\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", op.c_str(), argv[2], iterations, ms);

    xmlCleanupParser();
    return 0;
}
```

`benchmarks/libxml2/CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.16)
project(libxml2_bench)
set(CMAKE_CXX_STANDARD 17)
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBXML2 REQUIRED libxml-2.0)
add_executable(bench bench.cpp)
target_include_directories(bench PRIVATE ${LIBXML2_INCLUDE_DIRS})
target_link_libraries(bench ${LIBXML2_LIBRARIES})
```

`benchmarks/libxml2/Dockerfile`:
```dockerfile
FROM debian:bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake pkg-config libxml2-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY CMakeLists.txt bench.cpp ./
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j$(nproc)

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libxml2 time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bench /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 5: Commit all C++ benchmarks**

```bash
git add benchmarks/pugixml/ benchmarks/rapidxml/ benchmarks/expat/ benchmarks/libxml2/
git commit -m "feat: C++ benchmarks (pugixml, RapidXML, Expat, libxml2)"
```

---

### Task 6: Java Benchmarks (VTD-XML, Xerces, Woodstox)

**Files:**
- Create: `benchmarks/vtd-xml/{Dockerfile,pom.xml,src/main/java/bench/Bench.java}`
- Create: `benchmarks/xerces/{Dockerfile,pom.xml,src/main/java/bench/Bench.java}`
- Create: `benchmarks/woodstox/{Dockerfile,pom.xml,src/main/java/bench/Bench.java}`

- [ ] **Step 1: Create VTD-XML benchmark**

`benchmarks/vtd-xml/src/main/java/bench/Bench.java`:
```java
package bench;

import com.ximpleware.*;
import java.nio.file.Files;
import java.nio.file.Path;

public class Bench {
    public static void main(String[] args) throws Exception {
        if (args.length < 3) { System.err.println("Usage: bench <op> <file> <iterations>"); return; }
        String op = args[0], file = args[1];
        int iterations = Integer.parseInt(args[2]);
        byte[] xml = Files.readAllBytes(Path.of(file));

        if (op.equals("dom_parse")) {
            // Warmup
            for (int i = 0; i < Math.min(5, iterations); i++) {
                VTDGen vg = new VTDGen();
                vg.setDoc(xml.clone());
                vg.parse(false);
            }
            long start = System.nanoTime();
            for (int i = 0; i < iterations; i++) {
                VTDGen vg = new VTDGen();
                vg.setDoc(xml.clone());
                vg.parse(false);
            }
            double ms = (System.nanoTime() - start) / 1e6 / iterations;
            System.out.printf("{\"library\":\"VTD-XML\",\"language\":\"Java\",\"operation\":\"dom_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
        } else if (op.equals("xpath_query")) {
            VTDGen vg = new VTDGen();
            vg.setDoc(xml.clone());
            vg.parse(false);
            VTDNav vn = vg.getNav();
            // Warmup
            for (int i = 0; i < Math.min(5, iterations); i++) {
                AutoPilot ap = new AutoPilot(vn);
                ap.selectXPath("//*[@id]");
                int count = 0;
                while (ap.evalXPath() != -1) count++;
                vn.toElement(VTDNav.ROOT);
            }
            long start = System.nanoTime();
            for (int i = 0; i < iterations; i++) {
                AutoPilot ap = new AutoPilot(vn);
                ap.selectXPath("//*[@id]");
                int count = 0;
                while (ap.evalXPath() != -1) count++;
                vn.toElement(VTDNav.ROOT);
            }
            double ms = (System.nanoTime() - start) / 1e6 / iterations;
            System.out.printf("{\"library\":\"VTD-XML\",\"language\":\"Java\",\"operation\":\"xpath_query\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
        } else {
            System.out.printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"VTD-XML\"}%n", op);
        }
    }
}
```

`benchmarks/vtd-xml/pom.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>bench</groupId>
  <artifactId>vtd-xml-bench</artifactId>
  <version>1.0</version>
  <packaging>jar</packaging>
  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
  </properties>
  <dependencies>
    <dependency>
      <groupId>com.ximpleware</groupId>
      <artifactId>vtd-xml</artifactId>
      <version>2.13</version>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-shade-plugin</artifactId>
        <version>3.5.1</version>
        <executions>
          <execution>
            <phase>package</phase>
            <goals><goal>shade</goal></goals>
            <configuration>
              <transformers>
                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                  <mainClass>bench.Bench</mainClass>
                </transformer>
              </transformers>
            </configuration>
          </execution>
        </executions>
      </plugin>
    </plugins>
  </build>
</project>
```

`benchmarks/vtd-xml/Dockerfile`:
```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn dependency:resolve
COPY src/ src/
RUN mvn package -q -DskipTests

FROM eclipse-temurin:17-jre
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/vtd-xml-bench-1.0.jar /app/bench.jar
# Wrapper script to match the bench <op> <file> <iterations> interface
RUN printf '#!/bin/bash\njava -jar /app/bench.jar "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 2: Create Xerces benchmark**

`benchmarks/xerces/src/main/java/bench/Bench.java`:
```java
package bench;

import javax.xml.parsers.*;
import javax.xml.xpath.*;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.*;
import org.xml.sax.*;
import org.xml.sax.helpers.DefaultHandler;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;

public class Bench {
    public static void main(String[] args) throws Exception {
        if (args.length < 3) return;
        String op = args[0], file = args[1];
        int iterations = Integer.parseInt(args[2]);
        byte[] xml = Files.readAllBytes(Path.of(file));

        switch (op) {
            case "dom_parse" -> {
                DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
                // Warmup
                for (int i = 0; i < Math.min(5, iterations); i++) {
                    DocumentBuilder db = dbf.newDocumentBuilder();
                    db.parse(new ByteArrayInputStream(xml));
                }
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) {
                    DocumentBuilder db = dbf.newDocumentBuilder();
                    db.parse(new ByteArrayInputStream(xml));
                }
                double ms = (System.nanoTime() - start) / 1e6 / iterations;
                System.out.printf("{\"library\":\"Xerces\",\"language\":\"Java\",\"operation\":\"dom_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
            }
            case "sax_parse" -> {
                SAXParserFactory spf = SAXParserFactory.newInstance();
                DefaultHandler handler = new DefaultHandler();
                for (int i = 0; i < Math.min(5, iterations); i++) {
                    SAXParser sp = spf.newSAXParser();
                    sp.parse(new ByteArrayInputStream(xml), handler);
                }
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) {
                    SAXParser sp = spf.newSAXParser();
                    sp.parse(new ByteArrayInputStream(xml), handler);
                }
                double ms = (System.nanoTime() - start) / 1e6 / iterations;
                System.out.printf("{\"library\":\"Xerces\",\"language\":\"Java\",\"operation\":\"sax_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
            }
            case "xpath_query" -> {
                DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
                DocumentBuilder db = dbf.newDocumentBuilder();
                Document doc = db.parse(new ByteArrayInputStream(xml));
                XPathFactory xpf = XPathFactory.newInstance();
                for (int i = 0; i < Math.min(5, iterations); i++) {
                    XPath xp = xpf.newXPath();
                    NodeList nl = (NodeList) xp.evaluate("//*[@id]", doc, XPathConstants.NODESET);
                    int dummy = nl.getLength();
                }
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) {
                    XPath xp = xpf.newXPath();
                    NodeList nl = (NodeList) xp.evaluate("//*[@id]", doc, XPathConstants.NODESET);
                    int dummy = nl.getLength();
                }
                double ms = (System.nanoTime() - start) / 1e6 / iterations;
                System.out.printf("{\"library\":\"Xerces\",\"language\":\"Java\",\"operation\":\"xpath_query\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
            }
            case "serialize" -> {
                DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
                DocumentBuilder db = dbf.newDocumentBuilder();
                Document doc = db.parse(new ByteArrayInputStream(xml));
                TransformerFactory tf = TransformerFactory.newInstance();
                for (int i = 0; i < Math.min(5, iterations); i++) {
                    Transformer t = tf.newTransformer();
                    StringWriter sw = new StringWriter();
                    t.transform(new DOMSource(doc), new StreamResult(sw));
                }
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) {
                    Transformer t = tf.newTransformer();
                    StringWriter sw = new StringWriter();
                    t.transform(new DOMSource(doc), new StreamResult(sw));
                }
                double ms = (System.nanoTime() - start) / 1e6 / iterations;
                System.out.printf("{\"library\":\"Xerces\",\"language\":\"Java\",\"operation\":\"serialize\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
            }
            default -> System.out.printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"Xerces\"}%n", op);
        }
    }
}
```

`benchmarks/xerces/pom.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>bench</groupId>
  <artifactId>xerces-bench</artifactId>
  <version>1.0</version>
  <packaging>jar</packaging>
  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
  </properties>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-jar-plugin</artifactId>
        <version>3.3.0</version>
        <configuration>
          <archive><manifest><mainClass>bench.Bench</mainClass></manifest></archive>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

`benchmarks/xerces/Dockerfile`:
```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn dependency:resolve
COPY src/ src/
RUN mvn package -q -DskipTests

FROM eclipse-temurin:17-jre
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/xerces-bench-1.0.jar /app/bench.jar
RUN printf '#!/bin/bash\njava -jar /app/bench.jar "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 3: Create Woodstox benchmark**

`benchmarks/woodstox/src/main/java/bench/Bench.java`:
```java
package bench;

import com.ctc.wstx.stax.WstxInputFactory;
import javax.xml.stream.*;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;

public class Bench {
    public static void main(String[] args) throws Exception {
        if (args.length < 3) return;
        String op = args[0], file = args[1];
        int iterations = Integer.parseInt(args[2]);
        byte[] xml = Files.readAllBytes(Path.of(file));

        if (op.equals("sax_parse")) {
            WstxInputFactory factory = new WstxInputFactory();
            // Warmup
            for (int i = 0; i < Math.min(5, iterations); i++) {
                XMLStreamReader reader = factory.createXMLStreamReader(new ByteArrayInputStream(xml));
                while (reader.hasNext()) reader.next();
                reader.close();
            }
            long start = System.nanoTime();
            for (int i = 0; i < iterations; i++) {
                XMLStreamReader reader = factory.createXMLStreamReader(new ByteArrayInputStream(xml));
                while (reader.hasNext()) reader.next();
                reader.close();
            }
            double ms = (System.nanoTime() - start) / 1e6 / iterations;
            System.out.printf("{\"library\":\"Woodstox\",\"language\":\"Java\",\"operation\":\"sax_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
        } else {
            System.out.printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"Woodstox\"}%n", op);
        }
    }
}
```

`benchmarks/woodstox/pom.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>bench</groupId>
  <artifactId>woodstox-bench</artifactId>
  <version>1.0</version>
  <packaging>jar</packaging>
  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
  </properties>
  <dependencies>
    <dependency>
      <groupId>com.fasterxml.woodstox</groupId>
      <artifactId>woodstox-core</artifactId>
      <version>6.6.1</version>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-shade-plugin</artifactId>
        <version>3.5.1</version>
        <executions>
          <execution>
            <phase>package</phase>
            <goals><goal>shade</goal></goals>
            <configuration>
              <transformers>
                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                  <mainClass>bench.Bench</mainClass>
                </transformer>
              </transformers>
            </configuration>
          </execution>
        </executions>
      </plugin>
    </plugins>
  </build>
</project>
```

`benchmarks/woodstox/Dockerfile`:
```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn dependency:resolve
COPY src/ src/
RUN mvn package -q -DskipTests

FROM eclipse-temurin:17-jre
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/woodstox-bench-1.0.jar /app/bench.jar
RUN printf '#!/bin/bash\njava -jar /app/bench.jar "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 4: Commit all Java benchmarks**

```bash
git add benchmarks/vtd-xml/ benchmarks/xerces/ benchmarks/woodstox/
git commit -m "feat: Java benchmarks (VTD-XML, Xerces, Woodstox)"
```

---

### Task 7: Python Benchmarks (lxml, cElementTree)

**Files:**
- Create: `benchmarks/lxml/{Dockerfile,bench.py}`
- Create: `benchmarks/celementtree/{Dockerfile,bench.py}`

- [ ] **Step 1: Create lxml benchmark**

`benchmarks/lxml/bench.py`:
```python
#!/usr/bin/env python3
import sys
import time
import json
from lxml import etree

def bench_dom_parse(xml_bytes, iterations):
    start = time.perf_counter()
    for _ in range(iterations):
        etree.fromstring(xml_bytes)
    return (time.perf_counter() - start) * 1000 / iterations

def bench_xpath_query(xml_bytes, iterations):
    root = etree.fromstring(xml_bytes)
    start = time.perf_counter()
    for _ in range(iterations):
        root.xpath("//*[@id]")
    return (time.perf_counter() - start) * 1000 / iterations

def bench_serialize(xml_bytes, iterations):
    root = etree.fromstring(xml_bytes)
    start = time.perf_counter()
    for _ in range(iterations):
        etree.tostring(root, encoding="unicode")
    return (time.perf_counter() - start) * 1000 / iterations

def main():
    op, file_path, iterations = sys.argv[1], sys.argv[2], int(sys.argv[3])
    xml_bytes = open(file_path, "rb").read()
    funcs = {"dom_parse": bench_dom_parse, "xpath_query": bench_xpath_query, "serialize": bench_serialize}
    if op in funcs:
        ms = funcs[op](xml_bytes, iterations)
        print(json.dumps({"library": "lxml", "language": "Python", "operation": op, "file": file_path, "iterations": iterations, "time_ms": round(ms, 3)}))
    else:
        print(json.dumps({"skipped": True, "operation": op, "library": "lxml"}))

if __name__ == "__main__":
    main()
```

`benchmarks/lxml/Dockerfile`:
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir lxml
COPY bench.py /usr/local/bin/bench.py
RUN printf '#!/bin/bash\npython3 /usr/local/bin/bench.py "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 2: Create cElementTree benchmark**

`benchmarks/celementtree/bench.py`:
```python
#!/usr/bin/env python3
import sys
import time
import json
import xml.etree.ElementTree as ET

def bench_dom_parse(xml_bytes, iterations):
    start = time.perf_counter()
    for _ in range(iterations):
        ET.fromstring(xml_bytes)
    return (time.perf_counter() - start) * 1000 / iterations

def bench_serialize(xml_bytes, iterations):
    root = ET.fromstring(xml_bytes)
    start = time.perf_counter()
    for _ in range(iterations):
        ET.tostring(root, encoding="unicode")
    return (time.perf_counter() - start) * 1000 / iterations

def main():
    op, file_path, iterations = sys.argv[1], sys.argv[2], int(sys.argv[3])
    xml_bytes = open(file_path, "rb").read()
    funcs = {"dom_parse": bench_dom_parse, "serialize": bench_serialize}
    if op in funcs:
        ms = funcs[op](xml_bytes, iterations)
        print(json.dumps({"library": "cElementTree", "language": "Python", "operation": op, "file": file_path, "iterations": iterations, "time_ms": round(ms, 3)}))
    else:
        print(json.dumps({"skipped": True, "operation": op, "library": "cElementTree"}))

if __name__ == "__main__":
    main()
```

`benchmarks/celementtree/Dockerfile`:
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc && rm -rf /var/lib/apt/lists/*
COPY bench.py /usr/local/bin/bench.py
RUN printf '#!/bin/bash\npython3 /usr/local/bin/bench.py "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 3: Commit Python benchmarks**

```bash
git add benchmarks/lxml/ benchmarks/celementtree/
git commit -m "feat: Python benchmarks (lxml, cElementTree)"
```

---

### Task 8: Rust Benchmarks (quick-xml, roxmltree)

**Files:**
- Create: `benchmarks/quick-xml/{Dockerfile,Cargo.toml,src/main.rs}`
- Create: `benchmarks/roxmltree/{Dockerfile,Cargo.toml,src/main.rs}`

- [ ] **Step 1: Create quick-xml benchmark**

`benchmarks/quick-xml/Cargo.toml`:
```toml
[package]
name = "quick-xml-bench"
version = "0.1.0"
edition = "2021"

[dependencies]
quick-xml = "0.37"

[profile.release]
opt-level = 3
lto = true
```

`benchmarks/quick-xml/src/main.rs`:
```rust
use quick_xml::events::Event;
use quick_xml::reader::Reader;
use quick_xml::writer::Writer;
use std::env;
use std::fs;
use std::io::Cursor;
use std::time::Instant;

fn bench_dom_parse(xml: &[u8], iterations: usize) -> f64 {
    let start = Instant::now();
    for _ in 0..iterations {
        let mut reader = Reader::from_reader(xml);
        let mut buf = Vec::new();
        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Eof) => break,
                Err(e) => { eprintln!("Error: {e}"); break; }
                _ => {}
            }
            buf.clear();
        }
    }
    start.elapsed().as_secs_f64() * 1000.0 / iterations as f64
}

fn bench_sax_parse(xml: &[u8], iterations: usize) -> f64 {
    // quick-xml is inherently a pull parser, same as dom_parse traversal
    bench_dom_parse(xml, iterations)
}

fn bench_serialize(xml: &[u8], iterations: usize) -> f64 {
    // Read events once
    let mut events = Vec::new();
    let mut reader = Reader::from_reader(xml);
    let mut buf = Vec::new();
    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Eof) => break,
            Ok(e) => events.push(e.into_owned()),
            Err(_) => break,
        }
        buf.clear();
    }
    let start = Instant::now();
    for _ in 0..iterations {
        let mut writer = Writer::new(Cursor::new(Vec::new()));
        for event in &events {
            writer.write_event(event.clone()).ok();
        }
        let _ = writer.into_inner().into_inner().len();
    }
    start.elapsed().as_secs_f64() * 1000.0 / iterations as f64
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 { return; }
    let op = &args[1];
    let file = &args[2];
    let iterations: usize = args[3].parse().unwrap();
    let xml = fs::read(file).unwrap();

    match op.as_str() {
        "dom_parse" => {
            let ms = bench_dom_parse(&xml, iterations);
            println!("{{\"library\":\"quick-xml\",\"language\":\"Rust\",\"operation\":\"dom_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:.3}}}");
        }
        "sax_parse" => {
            let ms = bench_sax_parse(&xml, iterations);
            println!("{{\"library\":\"quick-xml\",\"language\":\"Rust\",\"operation\":\"sax_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:.3}}}");
        }
        "serialize" => {
            let ms = bench_serialize(&xml, iterations);
            println!("{{\"library\":\"quick-xml\",\"language\":\"Rust\",\"operation\":\"serialize\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:.3}}}");
        }
        _ => {
            println!("{{\"skipped\":true,\"operation\":\"{op}\",\"library\":\"quick-xml\"}}");
        }
    }
}
```

`benchmarks/quick-xml/Dockerfile`:
```dockerfile
FROM rust:1.78-slim AS build
WORKDIR /src
COPY Cargo.toml ./
COPY src/ src/
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/release/quick-xml-bench /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 2: Create roxmltree benchmark**

`benchmarks/roxmltree/Cargo.toml`:
```toml
[package]
name = "roxmltree-bench"
version = "0.1.0"
edition = "2021"

[dependencies]
roxmltree = "0.20"

[profile.release]
opt-level = 3
lto = true
```

`benchmarks/roxmltree/src/main.rs`:
```rust
use std::env;
use std::fs;
use std::time::Instant;

fn bench_dom_parse(xml: &str, iterations: usize) -> f64 {
    let start = Instant::now();
    for _ in 0..iterations {
        let _ = roxmltree::Document::parse(xml).unwrap();
    }
    start.elapsed().as_secs_f64() * 1000.0 / iterations as f64
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 { return; }
    let op = &args[1];
    let file = &args[2];
    let iterations: usize = args[3].parse().unwrap();
    let xml = fs::read_to_string(file).unwrap();

    match op.as_str() {
        "dom_parse" => {
            let ms = bench_dom_parse(&xml, iterations);
            println!("{{\"library\":\"roxmltree\",\"language\":\"Rust\",\"operation\":\"dom_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:.3}}}");
        }
        _ => {
            println!("{{\"skipped\":true,\"operation\":\"{op}\",\"library\":\"roxmltree\"}}");
        }
    }
}
```

`benchmarks/roxmltree/Dockerfile`:
```dockerfile
FROM rust:1.78-slim AS build
WORKDIR /src
COPY Cargo.toml ./
COPY src/ src/
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/release/roxmltree-bench /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 3: Commit Rust benchmarks**

```bash
git add benchmarks/quick-xml/ benchmarks/roxmltree/
git commit -m "feat: Rust benchmarks (quick-xml, roxmltree)"
```

---

### Task 9: C# Benchmark (System.Xml)

**Files:**
- Create: `benchmarks/system-xml/{Dockerfile,SystemXmlBench.csproj,Program.cs}`

- [ ] **Step 1: Create System.Xml benchmark**

`benchmarks/system-xml/SystemXmlBench.csproj`:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
```

`benchmarks/system-xml/Program.cs`:
```csharp
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Xml;
using System.Xml.Linq;
using System.Xml.XPath;

var op = args[0];
var file = args[1];
var iterations = int.Parse(args[2]);
var xmlBytes = File.ReadAllBytes(file);

switch (op)
{
    case "dom_parse":
    {
        // Warmup
        for (int i = 0; i < Math.Min(5, iterations); i++)
            XDocument.Load(new MemoryStream(xmlBytes));
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
            XDocument.Load(new MemoryStream(xmlBytes));
        sw.Stop();
        var ms = sw.Elapsed.TotalMilliseconds / iterations;
        Console.WriteLine($"{{\"library\":\"System.Xml\",\"language\":\"C#\",\"operation\":\"dom_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:F3}}}");
        break;
    }
    case "sax_parse":
    {
        for (int i = 0; i < Math.Min(5, iterations); i++)
        {
            using var reader = XmlReader.Create(new MemoryStream(xmlBytes));
            while (reader.Read()) { }
        }
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            using var reader = XmlReader.Create(new MemoryStream(xmlBytes));
            while (reader.Read()) { }
        }
        sw.Stop();
        var ms = sw.Elapsed.TotalMilliseconds / iterations;
        Console.WriteLine($"{{\"library\":\"System.Xml\",\"language\":\"C#\",\"operation\":\"sax_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:F3}}}");
        break;
    }
    case "xpath_query":
    {
        var doc = XDocument.Load(new MemoryStream(xmlBytes));
        for (int i = 0; i < Math.Min(5, iterations); i++)
            doc.XPathSelectElements("//*[@id]").GetEnumerator().MoveNext();
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            int count = 0;
            foreach (var _ in doc.XPathSelectElements("//*[@id]")) count++;
        }
        sw.Stop();
        var ms = sw.Elapsed.TotalMilliseconds / iterations;
        Console.WriteLine($"{{\"library\":\"System.Xml\",\"language\":\"C#\",\"operation\":\"xpath_query\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:F3}}}");
        break;
    }
    case "serialize":
    {
        var doc = XDocument.Load(new MemoryStream(xmlBytes));
        for (int i = 0; i < Math.Min(5, iterations); i++)
            doc.ToString();
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
            doc.ToString();
        sw.Stop();
        var ms = sw.Elapsed.TotalMilliseconds / iterations;
        Console.WriteLine($"{{\"library\":\"System.Xml\",\"language\":\"C#\",\"operation\":\"serialize\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:F3}}}");
        break;
    }
    default:
        Console.WriteLine($"{{\"skipped\":true,\"operation\":\"{op}\",\"library\":\"System.Xml\"}}");
        break;
}
```

`benchmarks/system-xml/Dockerfile`:
```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY SystemXmlBench.csproj Program.cs ./
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/runtime:8.0
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /app /app
RUN printf '#!/bin/bash\n/app/SystemXmlBench "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 2: Commit**

```bash
git add benchmarks/system-xml/
git commit -m "feat: C# benchmark (System.Xml)"
```

---

### Task 10: Go Benchmark (encoding/xml)

**Files:**
- Create: `benchmarks/encoding-xml/{Dockerfile,go.mod,main.go}`

- [ ] **Step 1: Create encoding/xml benchmark**

`benchmarks/encoding-xml/go.mod`:
```
module encoding-xml-bench

go 1.22
```

`benchmarks/encoding-xml/main.go`:
```go
package main

import (
	"bytes"
	"encoding/xml"
	"fmt"
	"io"
	"os"
	"strconv"
	"time"
)

func benchDOMParse(data []byte, iterations int) float64 {
	start := time.Now()
	for i := 0; i < iterations; i++ {
		var root interface{}
		xml.Unmarshal(data, &root)
	}
	return float64(time.Since(start).Microseconds()) / float64(iterations) / 1000.0
}

func benchSAXParse(data []byte, iterations int) float64 {
	start := time.Now()
	for i := 0; i < iterations; i++ {
		decoder := xml.NewDecoder(bytes.NewReader(data))
		for {
			_, err := decoder.Token()
			if err == io.EOF {
				break
			}
			if err != nil {
				break
			}
		}
	}
	return float64(time.Since(start).Microseconds()) / float64(iterations) / 1000.0
}

func benchSerialize(data []byte, iterations int) float64 {
	// Parse once, then serialize
	type Node struct {
		XMLName xml.Name
		Attrs   []xml.Attr `xml:",any,attr"`
		Content []byte     `xml:",chardata"`
		Children []Node    `xml:",any"`
	}
	var root Node
	xml.Unmarshal(data, &root)
	start := time.Now()
	for i := 0; i < iterations; i++ {
		xml.Marshal(root)
	}
	return float64(time.Since(start).Microseconds()) / float64(iterations) / 1000.0
}

func main() {
	if len(os.Args) < 4 {
		return
	}
	op := os.Args[1]
	file := os.Args[2]
	iterations, _ := strconv.Atoi(os.Args[3])
	data, _ := os.ReadFile(file)

	switch op {
	case "dom_parse":
		ms := benchDOMParse(data, iterations)
		fmt.Printf(`{"library":"encoding/xml","language":"Go","operation":"dom_parse","file":"%s","iterations":%d,"time_ms":%.3f}`+"\n", file, iterations, ms)
	case "sax_parse":
		ms := benchSAXParse(data, iterations)
		fmt.Printf(`{"library":"encoding/xml","language":"Go","operation":"sax_parse","file":"%s","iterations":%d,"time_ms":%.3f}`+"\n", file, iterations, ms)
	case "serialize":
		ms := benchSerialize(data, iterations)
		fmt.Printf(`{"library":"encoding/xml","language":"Go","operation":"serialize","file":"%s","iterations":%d,"time_ms":%.3f}`+"\n", file, iterations, ms)
	default:
		fmt.Printf(`{"skipped":true,"operation":"%s","library":"encoding/xml"}`+"\n", op)
	}
}
```

`benchmarks/encoding-xml/Dockerfile`:
```dockerfile
FROM golang:1.22-bookworm AS build
WORKDIR /src
COPY go.mod main.go ./
RUN CGO_ENABLED=0 go build -o bench .

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/bench /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 2: Commit**

```bash
git add benchmarks/encoding-xml/
git commit -m "feat: Go benchmark (encoding/xml)"
```

---

### Task 11: JavaScript Benchmark (fast-xml-parser)

**Files:**
- Create: `benchmarks/fast-xml-parser/{Dockerfile,package.json,bench.js}`

- [ ] **Step 1: Create fast-xml-parser benchmark**

`benchmarks/fast-xml-parser/package.json`:
```json
{
  "name": "fast-xml-parser-bench",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "fast-xml-parser": "^4.3.0"
  }
}
```

`benchmarks/fast-xml-parser/bench.js`:
```javascript
const fs = require("fs");
const { XMLParser, XMLBuilder } = require("fast-xml-parser");

const op = process.argv[2];
const file = process.argv[3];
const iterations = parseInt(process.argv[4], 10);
const xml = fs.readFileSync(file, "utf-8");

if (op === "dom_parse") {
  const parser = new XMLParser({ ignoreAttributes: false });
  // Warmup
  for (let i = 0; i < Math.min(5, iterations); i++) parser.parse(xml);
  const start = process.hrtime.bigint();
  for (let i = 0; i < iterations; i++) parser.parse(xml);
  const ms = Number(process.hrtime.bigint() - start) / 1e6 / iterations;
  console.log(JSON.stringify({ library: "fast-xml-parser", language: "JS", operation: "dom_parse", file, iterations, time_ms: +ms.toFixed(3) }));
} else if (op === "serialize") {
  const parser = new XMLParser({ ignoreAttributes: false });
  const obj = parser.parse(xml);
  const builder = new XMLBuilder({ ignoreAttributes: false });
  for (let i = 0; i < Math.min(5, iterations); i++) builder.build(obj);
  const start = process.hrtime.bigint();
  for (let i = 0; i < iterations; i++) builder.build(obj);
  const ms = Number(process.hrtime.bigint() - start) / 1e6 / iterations;
  console.log(JSON.stringify({ library: "fast-xml-parser", language: "JS", operation: "serialize", file, iterations, time_ms: +ms.toFixed(3) }));
} else {
  console.log(JSON.stringify({ skipped: true, operation: op, library: "fast-xml-parser" }));
}
```

`benchmarks/fast-xml-parser/Dockerfile`:
```dockerfile
FROM node:20-slim AS build
WORKDIR /src
COPY package.json ./
RUN npm install --production

FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends time bc python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/node_modules /app/node_modules
COPY bench.js /app/bench.js
COPY package.json /app/package.json
RUN printf '#!/bin/bash\nnode /app/bench.js "$@"\n' > /usr/local/bin/bench && chmod +x /usr/local/bin/bench
COPY ../runner.sh /usr/local/bin/runner.sh
RUN chmod +x /usr/local/bin/runner.sh
ENTRYPOINT ["/usr/local/bin/runner.sh", "/usr/local/bin/bench"]
```

- [ ] **Step 2: Commit**

```bash
git add benchmarks/fast-xml-parser/
git commit -m "feat: JavaScript benchmark (fast-xml-parser)"
```

---

### Task 12: Orchestrator

**Files:**
- Create: `tools/orchestrator.py`

- [ ] **Step 1: Create orchestrator.py**

```python
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
    """Build Docker image for a library. Returns image tag."""
    tag = f"xmlbench-{lib['dir']}"
    bench_dir = os.path.join(BENCHMARKS_DIR, lib["dir"])
    # Copy runner.sh into the build context
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
    # Clean up copied runner.sh
    os.remove(runner_dst)
    return tag


def build_all_images():
    """Build all Docker images in parallel."""
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
    """Choose iteration count so total runtime >= 2s."""
    if file_size_bytes > 50_000_000:
        return 1
    elif file_size_bytes > 5_000_000:
        return 5
    elif file_size_bytes > 500_000:
        return 20
    elif file_size_bytes > 50_000:
        return 100
    else:
        return 500


def run_benchmark(lib: dict, operation: str, data_file: str, iterations: int):
    """Run a single benchmark container."""
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
    """List all XML test files."""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.xml")))
    return files


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    # Clear previous results
    results_file = os.path.join(RESULTS_DIR, "results.jsonl")
    if os.path.exists(results_file):
        os.remove(results_file)

    # Generate data if needed
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
```

- [ ] **Step 2: Commit**

```bash
git add tools/orchestrator.py
git commit -m "feat: benchmark orchestrator (Docker build, sequential run, data collection)"
```

---

### Task 13: Report Generator

**Files:**
- Create: `tools/report_generator.py`

- [ ] **Step 1: Create report_generator.py**

```python
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
    """Load all JSONL results."""
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
    """Extract size label from filename like 'wide_10MB.xml'."""
    for s in SIZES:
        if s in filename:
            return s
    return "other"


def build_benchmark_data(results: list[dict]) -> dict:
    """Transform flat results into the BENCHMARK_DATA structure expected by index.html."""
    # Group: results[op_label][size_label] = [ {library, time_ms, throughput_mbs, memory_mb, cpu_ms} ]
    grouped = defaultdict(lambda: defaultdict(list))
    for r in results:
        op_label = OPERATION_LABELS.get(r["operation"], r["operation"])
        fname = os.path.basename(r.get("file", ""))
        size_label = size_label_from_filename(fname)
        grouped[op_label][size_label].append({
            "library": r["library"],
            "time_ms": r.get("time_ms", 0),
            "throughput_mbs": r.get("throughput_mbs", 0),
            "memory_mb": r.get("peak_rss_mb", 0),
            "cpu_ms": round(r.get("cpu_user_ms", 0) + r.get("cpu_system_ms", 0), 3),
        })

    # Sort each group by time
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
    """Replace the BENCHMARK_DATA block in the HTML template."""
    template_path = os.path.join(ROOT, REPORT_TEMPLATE)
    with open(template_path) as f:
        html = f.read()

    data_json = json.dumps(data, indent=2)

    # Replace the generateSampleData() call and the entire BENCHMARK_DATA block
    # Pattern: const BENCHMARK_DATA = { ... generateSampleData() ... };
    # Replace with: const BENCHMARK_DATA = <actual data>;
    pattern = r"const BENCHMARK_DATA = \{[\s\S]*?generateSampleData\(\)[\s\S]*?\};"
    replacement = f"const BENCHMARK_DATA = {data_json};"
    html = re.sub(pattern, replacement, html)

    # Remove the generateSampleData function
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
```

- [ ] **Step 2: Commit**

```bash
git add tools/report_generator.py
git commit -m "feat: report generator (JSONL -> HTML with real data injection)"
```

---

### Task 14: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/benchmark.yml`

- [ ] **Step 1: Create workflow file**

```yaml
name: XML Benchmark

on:
  schedule:
    - cron: '0 0 1 * *'  # 1st of each month at midnight UTC
  workflow_dispatch:       # Manual trigger

permissions:
  contents: write
  pages: write

jobs:
  benchmark:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Run benchmarks
        env:
          RUNNER_INFO: "ubuntu-latest / GitHub Actions"
        run: python tools/orchestrator.py

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./report
          force_orphan: true
```

- [ ] **Step 2: Commit**

```bash
mkdir -p .github/workflows
git add .github/workflows/benchmark.yml
git commit -m "ci: GitHub Actions workflow (monthly cron + manual trigger, deploys to Pages)"
```

---

### Task 15: Fix Docker COPY for runner.sh

The Dockerfiles reference `COPY ../runner.sh` which won't work with Docker's build context. The orchestrator already handles this by copying `runner.sh` into each build context before building. But the Dockerfiles need to reference it as a local file.

**Files:**
- Modify: All Dockerfiles

- [ ] **Step 1: Update all Dockerfiles to use `COPY runner.sh` instead of `COPY ../runner.sh`**

In every Dockerfile, change:
```dockerfile
COPY ../runner.sh /usr/local/bin/runner.sh
```
to:
```dockerfile
COPY runner.sh /usr/local/bin/runner.sh
```

This applies to all 14 Dockerfiles in `benchmarks/*/Dockerfile`.

- [ ] **Step 2: Commit**

```bash
git add benchmarks/*/Dockerfile
git commit -m "fix: Dockerfiles reference runner.sh from local build context"
```

---

### Task 16: End-to-End Verification

- [ ] **Step 1: Generate test data**

```bash
cd /c/Users/mayer/Documents/xml-benchmark
python tools/generate_data.py
```

Expected: 10 XML files in `data/`, sizes from ~1KB to ~100MB.

- [ ] **Step 2: Build and test one container (pugixml)**

```bash
cp benchmarks/runner.sh benchmarks/pugixml/runner.sh
docker build -t xmlbench-pugixml benchmarks/pugixml/
mkdir -p results
docker run --rm -v "$(pwd)/data:/data:ro" -v "$(pwd)/results:/results" xmlbench-pugixml dom_parse /data/wide_1KB.xml 100 /results
cat results/results.jsonl
rm benchmarks/pugixml/runner.sh
```

Expected: JSON line with library, time_ms, peak_rss_mb, etc.

- [ ] **Step 3: Run full orchestrator** (requires Docker, takes ~30-60 min)

```bash
python tools/orchestrator.py
```

- [ ] **Step 4: Verify report**

Open `report/index.html` in a browser. Confirm charts show real data, table is sortable, filters work.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: final verification pass"
```
