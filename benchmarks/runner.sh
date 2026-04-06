#!/usr/bin/env bash
# runner.sh — wraps a benchmark binary, captures system metrics, enriches JSON output
# Usage: runner.sh <benchmark_cmd> <operation> <input_file> <iterations> <output_dir>
set -euo pipefail

BENCH_CMD="$1"
OPERATION="$2"
INPUT_FILE="$3"
ITERATIONS="$4"
OUTPUT_DIR="$5"

BENCH_OUTPUT=$(mktemp)
TIME_OUTPUT=$(mktemp)

# Single run: /usr/bin/time for RSS, bash time builtin for precise CPU
# We use both: GNU time captures RSS, and we wrap with bash time for ms-precision CPU
/usr/bin/time -v -o "$TIME_OUTPUT" bash -c '
  TIMEFORMAT="%3U %3S"
  CPU=$( { time "$1" "$2" "$3" "$4" > "$5" 2>/dev/null ; } 2>&1 ) || true
  echo "$CPU" > "$5.cpu"
' _ "$BENCH_CMD" "$OPERATION" "$INPUT_FILE" "$ITERATIONS" "$BENCH_OUTPUT" 2>/dev/null || true

# Parse bash time output (user sys in seconds, 3 decimal places)
if [ -f "$BENCH_OUTPUT.cpu" ]; then
  USER_SEC=$(awk '{print $1}' "$BENCH_OUTPUT.cpu")
  SYS_SEC=$(awk '{print $2}' "$BENCH_OUTPUT.cpu")
  rm -f "$BENCH_OUTPUT.cpu"
else
  # Fallback to GNU time (less precise)
  USER_SEC=$(grep "User time" "$TIME_OUTPUT" | awk '{print $NF}')
  SYS_SEC=$(grep "System time" "$TIME_OUTPUT" | awk '{print $NF}')
fi

# RSS from GNU time
RSS_KB=$(grep "Maximum resident set size" "$TIME_OUTPUT" | awk '{print $NF}')

# Convert
RSS_MB=$(echo "scale=1; ${RSS_KB:-0} / 1024" | bc)
USER_MS=$(echo "scale=3; ${USER_SEC:-0} * 1000" | bc)
SYS_MS=$(echo "scale=3; ${SYS_SEC:-0} * 1000" | bc)
FILE_SIZE=$(stat -c%s "$INPUT_FILE" 2>/dev/null || stat -f%z "$INPUT_FILE")

# Read the benchmark's JSON output line and enrich it
if [ -s "$BENCH_OUTPUT" ]; then
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
