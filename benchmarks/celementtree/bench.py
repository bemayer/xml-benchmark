#!/usr/bin/env python3
import sys, time, json
import xml.etree.ElementTree as ET

def bench_dom_parse(xml_bytes, iterations):
    start = time.perf_counter()
    for _ in range(iterations): ET.fromstring(xml_bytes)
    return (time.perf_counter() - start) * 1000 / iterations

def bench_serialize(xml_bytes, iterations):
    root = ET.fromstring(xml_bytes)
    start = time.perf_counter()
    for _ in range(iterations): ET.tostring(root, encoding="unicode")
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

if __name__ == "__main__": main()
