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
