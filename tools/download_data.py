#!/usr/bin/env python3
"""Download real-world XML test files."""

import os
import sys
import urllib.request
import gzip
import shutil

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA_DIR

DATASETS = [
    {
        "name": "dblp_10MB",
        "url": "https://dblp.org/xml/release/dblp-2024-01-01.xml.gz",
        "filename": "realworld_dblp.xml",
        "max_bytes": 10 * 1024 * 1024,
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
                    raw = resp.read()
                    decompressed = gzip.decompress(raw)
                    chunk = decompressed[: dataset["max_bytes"]]
                    last_close = chunk.rfind(b"</")
                    if last_close > 0:
                        end = chunk.find(b">", last_close)
                        if end > 0:
                            chunk = chunk[: end + 1]
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
