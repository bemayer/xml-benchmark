#!/usr/bin/env python3
import sys, time, json
from lxml import etree

def bench_dom_parse(xml_bytes, iterations):
    start = time.perf_counter()
    for _ in range(iterations): etree.fromstring(xml_bytes)
    return (time.perf_counter() - start) * 1000 / iterations

def bench_xpath_query(xml_bytes, iterations):
    root = etree.fromstring(xml_bytes)
    start = time.perf_counter()
    for _ in range(iterations): root.xpath("//*[@id]")
    return (time.perf_counter() - start) * 1000 / iterations

def bench_serialize(xml_bytes, iterations):
    root = etree.fromstring(xml_bytes)
    start = time.perf_counter()
    for _ in range(iterations): etree.tostring(root, encoding="unicode")
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

if __name__ == "__main__": main()
