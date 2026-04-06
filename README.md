# XML Benchmark

Cross-language benchmark of the fastest XML parsing libraries. Compares **14 libraries** across **7 languages**, measuring parse speed, memory usage, and CPU time.

**[View the live report](https://bemayer.github.io/xml-benchmark/)**

Results are published automatically to GitHub Pages on the 1st of each month.

## Libraries

| Language | Library | Operations |
|----------|---------|------------|
| C++ | pugixml | DOM Parse, XPath, Serialize |
| C++ | RapidXML | DOM Parse, Serialize |
| C++ | Expat | SAX/Stream |
| C++ | libxml2 | DOM Parse, SAX/Stream, XPath, Serialize |
| Java | VTD-XML | DOM Parse, XPath |
| Java | Xerces | DOM Parse, SAX/Stream, XPath, Serialize |
| Java | Woodstox | SAX/Stream (StAX) |
| Python | lxml | DOM Parse, XPath, Serialize |
| Python | cElementTree | DOM Parse, Serialize |
| Rust | quick-xml | DOM Parse, SAX/Stream, Serialize |
| Rust | roxmltree | DOM Parse |
| C# | System.Xml | DOM Parse, SAX/Stream, XPath, Serialize |
| Go | encoding/xml | DOM Parse, SAX/Stream, Serialize |
| JS | fast-xml-parser | DOM Parse, Serialize |

## Metrics

Each benchmark measures:
- **Wall-clock time** (median of N iterations, auto-calibrated)
- **Peak RSS memory**
- **CPU time** (user + system)
- **Throughput** (MB/s)

## Test data

**Synthetic** XML files at 5 sizes (1KB, 100KB, 1MB, 10MB, 100MB) in two shapes:
- **Wide/shallow**: many sibling elements, few levels deep
- **Deep/narrow**: deeply nested, few siblings per level

**Real-world** extracts (~10MB each):
- DBLP (academic publications)
- OpenStreetMap (geographic data)

All test data is generated fresh before each run and is not stored in the repository.

## How it works

Each library runs in its own Docker container for isolation. A shared `runner.sh` wrapper captures system-level metrics via GNU `time`. All libraries use the latest available versions, and Docker base images are pulled fresh on each run.

```
tools/orchestrator.py
  1. Generate synthetic XML data
  2. Download real-world XML data
  3. Build Docker images (parallel, --pull --no-cache)
  4. Run benchmarks (sequential, to avoid resource contention)
  5. Collect JSON results
  6. Generate HTML report
```

## Running locally

**Requirements:** Docker, Python 3.10+

```bash
# Run the full benchmark suite
python tools/orchestrator.py

# Or run individual steps:
python tools/generate_data.py        # Generate test data
python tools/download_data.py        # Download real-world data
python tools/report_generator.py     # Regenerate report from existing results
```

The full suite takes 30-60 minutes depending on hardware. Results are written to `results/results.jsonl` and the HTML report to `report/index.html`.

## Report

The HTML report features:
- Podium visualization of the top 3 fastest libraries
- Bar charts comparing parse time, throughput, memory, and CPU
- Interactive filters by file size and operation type
- Sortable results table with all metrics
- Per-language color coding

## CI/CD

GitHub Actions runs the benchmark on the 1st of each month (and on manual trigger). Results are deployed to GitHub Pages automatically.

```yaml
on:
  schedule:
    - cron: '0 0 1 * *'
  workflow_dispatch:
```

## Project structure

```
benchmarks/           # One directory per library (Dockerfile + benchmark code)
  runner.sh           # Shared wrapper for system metrics capture
tools/
  common.py           # Shared constants (libraries, sizes, operations)
  generate_data.py    # Synthetic XML generator
  download_data.py    # Real-world XML downloader
  orchestrator.py     # Builds and runs all benchmarks
  report_generator.py # Generates HTML report from results
report/
  index.html          # Interactive HTML report (Chart.js)
.github/workflows/
  benchmark.yml       # Monthly cron + manual trigger
```

## Adding a library

1. Create `benchmarks/<name>/` with a `Dockerfile` and benchmark code
2. The benchmark binary must accept: `<operation> <input_file> <iterations>`
3. Output one JSON line per invocation to stdout:
   ```json
   {"library":"name","language":"Lang","operation":"dom_parse","file":"...","iterations":N,"time_ms":0.123}
   ```
4. For unsupported operations, output: `{"skipped":true,"operation":"...","library":"name"}`
5. Add the library to `LIBRARIES` in `tools/common.py`
6. Add a `COPY runner.sh` line in the Dockerfile

## License

MIT
