#include <expat.h>
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

static void start_element(void*, const XML_Char*, const XML_Char**) {}
static void end_element(void*, const XML_Char*) {}
static void char_data(void*, const XML_Char*, int) {}

double bench_sax_parse(const std::string& xml, int iterations) {
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        XML_Parser parser = XML_ParserCreate(nullptr);
        XML_SetElementHandler(parser, start_element, end_element);
        XML_SetCharacterDataHandler(parser, char_data);
        XML_Parse(parser, xml.c_str(), xml.size(), XML_TRUE);
        XML_ParserFree(parser);
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

int main(int argc, char* argv[]) {
    if (argc < 4) return 1;
    std::string op = argv[1];
    std::string xml = read_file(argv[2]);
    int iterations = std::stoi(argv[3]);

    if (op == "sax_parse") {
        double ms = bench_sax_parse(xml, iterations);
        printf("{\"library\":\"Expat\",\"language\":\"C++\",\"operation\":\"sax_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", argv[2], iterations, ms);
    } else {
        printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"Expat\"}\n", op.c_str());
    }
    return 0;
}
