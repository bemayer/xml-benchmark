#!/usr/bin/env bash
# runner.sh — wraps a benchmark binary, captures system metrics, enriches JSON output
# Usage: runner.sh <benchmark_cmd> <operation> <input_file> <iterations> <output_dir>
set -euo pipefail

BENCH_CMD="$1"
OPERATION="$2"
INPUT_FILE="$3"
ITERATIONS="$4"
OUTPUT_DIR="$5"

# Run benchmark under /usr/bin/time for RSS + CPU, capture stdout for JSON
TIME_OUTPUT=$(mktemp)
BENCH_OUTPUT=$(mktemp)

/usr/bin/time -v -o "$TIME_OUTPUT" \
  "$BENCH_CMD" "$OPERATION" "$INPUT_FILE" "$ITERATIONS" > "$BENCH_OUTPUT" 2>/dev/null || true

# Parse /usr/bin/time output
RSS_KB=$(grep "Maximum resident set size" "$TIME_OUTPUT" | awk '{print $NF}')
USER_SEC=$(grep "User time" "$TIME_OUTPUT" | awk '{print $NF}')
SYS_SEC=$(grep "System time" "$TIME_OUTPUT" | awk '{print $NF}')

FILE_SIZE=$(stat -c%s "$INPUT_FILE" 2>/dev/null || stat -f%z "$INPUT_FILE")

# Enrich JSON with system metrics
if [ -s "$BENCH_OUTPUT" ]; then
  python3 -c "
import json
user_ms = round(float('$USER_SEC') * 1000, 1)
sys_ms = round(float('$SYS_SEC') * 1000, 1)
rss_mb = round(float('${RSS_KB:-0}') / 1024, 1)
file_size = int('$FILE_SIZE')
for line in open('$BENCH_OUTPUT'):
    line = line.strip()
    if not line or not line.startswith('{'):
        continue
    data = json.loads(line)
    if data.get('skipped'):
        print(json.dumps(data))
        continue
    data['peak_rss_mb'] = rss_mb
    data['cpu_user_ms'] = user_ms
    data['cpu_system_ms'] = sys_ms
    data['file_size_bytes'] = file_size
    time_s = data.get('time_ms', 0) / 1000
    if time_s > 0:
        data['throughput_mbs'] = round(file_size / 1048576 / time_s, 1)
    print(json.dumps(data))
" >> "$OUTPUT_DIR/results.jsonl"
fi

rm -f "$TIME_OUTPUT" "$BENCH_OUTPUT"
