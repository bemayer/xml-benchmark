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
