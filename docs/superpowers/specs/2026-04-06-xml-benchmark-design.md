# XML Benchmark Suite — Design Spec

## Context

We want a cross-language benchmark of the fastest XML libraries to produce a public, regularly-updated comparison. Results are published as a static HTML report to GitHub Pages, regenerated monthly via GitHub Actions.

## Libraries

| Language | Library | Parse Model |
|----------|---------|-------------|
| C++ | pugixml | DOM |
| C++ | RapidXML | DOM (in-situ) |
| C++ | Expat | SAX/streaming |
| C++ | libxml2 | DOM + SAX |
| Java | VTD-XML | Virtual Token Descriptor |
| Java | Xerces | DOM + SAX |
| Java | Woodstox | StAX streaming |
| Python | lxml | DOM + XPath |
| Python | xml.etree (cElementTree) | DOM |
| Rust | quick-xml | Pull parser |
| Rust | roxmltree | DOM (read-only) |
| C# | System.Xml (.NET) | DOM + Reader |
| Go | encoding/xml | Streaming |
| JavaScript | fast-xml-parser | DOM |

## Operations (benchmarked independently)

1. **DOM Parse** — parse XML into tree. All libraries.
2. **SAX/Stream Parse** — event-driven parse. Libraries that support it (Expat, libxml2, Xerces, Woodstox, quick-xml, System.Xml XmlReader, encoding/xml).
3. **XPath Query** — query a pre-parsed document. Libraries with XPath support (pugixml, libxml2, lxml, VTD-XML, Xerces, System.Xml).
4. **Serialization** — write tree back to XML string. DOM libraries only.

## Test Data

### Synthetic (generated at build time)
- Sizes: 1KB, 100KB, 1MB, 10MB, 100MB
- Two shapes per size:
  - **Wide/shallow**: many sibling elements, few levels deep
  - **Deep/narrow**: deeply nested, few siblings
- Generator: Python script in `tools/generate_data.py`

### Real-world
- **DBLP** extract (~10MB subset)
- **OpenStreetMap** extract (~10MB subset)
- Downloaded at build time; cached in Docker volume

## Metrics (per run)

- **Wall-clock time**: median of N iterations (N auto-calibrated so total run >= 2s)
- **Peak RSS memory**: measured via `/usr/bin/time -v` or language-specific API
- **CPU time**: user + system
- **Throughput**: derived as file_size / wall_time (MB/s)

Results output as JSON per library per operation per file.

## Architecture

```
xml-benchmark/
  benchmarks/
    pugixml/
      Dockerfile
      bench.cpp
      CMakeLists.txt
    rapidxml/
      ...
    ...one dir per library...
  tools/
    generate_data.py       # synthetic XML generator
    orchestrator.py        # builds images, runs containers, collects JSON
    report_generator.py    # JSON -> static HTML
  report/
    index.html             # generated, not committed (built in CI)
    chart.js / styles
  data/                    # generated/downloaded test files (gitignored)
  .github/
    workflows/
      benchmark.yml        # cron: 1st of each month + manual trigger
  docs/
    superpowers/specs/     # this spec
```

### Docker setup
- Each library has its own Dockerfile based on a minimal image (alpine/debian-slim).
- Dockerfile installs deps, compiles benchmark binary, copies it to final stage (multi-stage).
- Container entry point: run benchmark, write JSON results to mounted volume.

### Orchestrator (`tools/orchestrator.py`)
1. Generate synthetic data (if not cached).
2. Download real-world data (if not cached).
3. Build all Docker images (parallelized).
4. Run each container sequentially (to avoid resource contention skewing results).
5. Collect JSON results from output volume.
6. Invoke report generator.

### Report (`tools/report_generator.py`)
- Reads all JSON result files.
- Uses `report/index.html` as the template (already built with Chart.js charts, sortable table, podium, filters).
- Injects the `BENCHMARK_DATA` JSON object into the template.
- Output to `report/` directory.

### GitHub Actions (`.github/workflows/benchmark.yml`)
- **Cron trigger**: `0 0 1 * *` (midnight UTC, 1st of each month)
- **Manual trigger**: `workflow_dispatch`
- Steps: checkout, run orchestrator, deploy `report/` to `gh-pages` branch
- Runner: `ubuntu-latest` (consistent hardware baseline)

## Verification

1. Run `python tools/generate_data.py` — confirm synthetic XML files are created at expected sizes.
2. Build and run a single library container (e.g., pugixml) — confirm JSON output with all metrics.
3. Run `python tools/orchestrator.py` — confirm all containers run and results are collected.
4. Run `python tools/report_generator.py` — confirm HTML report renders correctly in browser.
5. Push to GitHub — confirm Actions workflow runs and deploys to Pages.
