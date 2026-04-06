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
    overhead_per_level = 60
    depth = max(1, target_bytes // overhead_per_level)
    depth = min(depth, 5000)
    parts = ['<?xml version="1.0" encoding="UTF-8"?>\n']
    for i in range(depth):
        indent = "  " * i
        parts.append(f'{indent}<level id="{i}" depth="{i}">\n')
    current_size = sum(len(p.encode()) for p in parts)
    close_size = sum(len(("  " * i + "</level>\n").encode()) for i in range(depth - 1, -1, -1))
    remaining = target_bytes - current_size - close_size
    if remaining > 0:
        indent = "  " * depth
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
