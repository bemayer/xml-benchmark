#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/xpath.h>
#include <libxml/xmlsave.h>
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

static void sax_start(void*, const xmlChar*, const xmlChar**) {}
static void sax_end(void*, const xmlChar*) {}
static void sax_chars(void*, const xmlChar*, int) {}

double bench_dom_parse(const std::string& xml, int iterations) {
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        xmlDocPtr doc = xmlParseMemory(xml.c_str(), xml.size());
        xmlFreeDoc(doc);
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_sax_parse(const std::string& xml, int iterations) {
    xmlSAXHandler handler = {};
    handler.startElement = sax_start;
    handler.endElement = sax_end;
    handler.characters = sax_chars;
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        xmlSAXUserParseMemory(&handler, nullptr, xml.c_str(), xml.size());
    }
    auto end = Clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_xpath_query(const std::string& xml, int iterations) {
    xmlDocPtr doc = xmlParseMemory(xml.c_str(), xml.size());
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        xmlXPathContextPtr ctx = xmlXPathNewContext(doc);
        xmlXPathObjectPtr result = xmlXPathEvalExpression((const xmlChar*)"//*[@id]", ctx);
        volatile int count = result ? result->nodesetval->nodeNr : 0;
        (void)count;
        xmlXPathFreeObject(result);
        xmlXPathFreeContext(ctx);
    }
    auto end = Clock::now();
    xmlFreeDoc(doc);
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

double bench_serialize(const std::string& xml, int iterations) {
    xmlDocPtr doc = xmlParseMemory(xml.c_str(), xml.size());
    auto start = Clock::now();
    for (int i = 0; i < iterations; i++) {
        xmlChar* buf = nullptr;
        int size = 0;
        xmlDocDumpMemory(doc, &buf, &size);
        volatile int len = size;
        (void)len;
        xmlFree(buf);
    }
    auto end = Clock::now();
    xmlFreeDoc(doc);
    return std::chrono::duration<double, std::milli>(end - start).count() / iterations;
}

int main(int argc, char* argv[]) {
    if (argc < 4) return 1;
    std::string op = argv[1];
    std::string xml = read_file(argv[2]);
    int iterations = std::stoi(argv[3]);
    xmlInitParser();

    double ms = 0;
    bool skipped = false;
    if (op == "dom_parse") ms = bench_dom_parse(xml, iterations);
    else if (op == "sax_parse") ms = bench_sax_parse(xml, iterations);
    else if (op == "xpath_query") ms = bench_xpath_query(xml, iterations);
    else if (op == "serialize") ms = bench_serialize(xml, iterations);
    else skipped = true;

    if (skipped)
        printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"libxml2\"}\n", op.c_str());
    else
        printf("{\"library\":\"libxml2\",\"language\":\"C++\",\"operation\":\"%s\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", op.c_str(), argv[2], iterations, ms);

    xmlCleanupParser();
    return 0;
}
