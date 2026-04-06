"""Shared constants for the XML benchmark suite."""

SIZES = ["1KB", "100KB", "1MB", "10MB", "100MB"]

SIZE_BYTES = {
    "1KB": 1024,
    "100KB": 102_400,
    "1MB": 1_048_576,
    "10MB": 10_485_760,
    "100MB": 104_857_600,
}

OPERATIONS = ["dom_parse", "sax_parse", "xpath_query", "serialize"]

OPERATION_LABELS = {
    "dom_parse": "DOM Parse",
    "sax_parse": "SAX/Stream",
    "xpath_query": "XPath Query",
    "serialize": "Serialize",
}

LIBRARIES = [
    {"name": "pugixml",         "dir": "pugixml",         "lang": "C++",    "lang_class": "cpp",    "ops": ["dom_parse", "xpath_query", "serialize"]},
    {"name": "RapidXML",        "dir": "rapidxml",        "lang": "C++",    "lang_class": "cpp",    "ops": ["dom_parse", "serialize"]},
    {"name": "Expat",           "dir": "expat",           "lang": "C++",    "lang_class": "cpp",    "ops": ["sax_parse"]},
    {"name": "libxml2",         "dir": "libxml2",         "lang": "C++",    "lang_class": "cpp",    "ops": ["dom_parse", "sax_parse", "xpath_query", "serialize"]},
    {"name": "VTD-XML",         "dir": "vtd-xml",         "lang": "Java",   "lang_class": "java",   "ops": ["dom_parse", "xpath_query"]},
    {"name": "Xerces",          "dir": "xerces",          "lang": "Java",   "lang_class": "java",   "ops": ["dom_parse", "sax_parse", "xpath_query", "serialize"]},
    {"name": "Woodstox",        "dir": "woodstox",        "lang": "Java",   "lang_class": "java",   "ops": ["sax_parse"]},
    {"name": "lxml",            "dir": "lxml",            "lang": "Python", "lang_class": "python", "ops": ["dom_parse", "xpath_query", "serialize"]},
    {"name": "cElementTree",    "dir": "celementtree",    "lang": "Python", "lang_class": "python", "ops": ["dom_parse", "serialize"]},
    {"name": "quick-xml",       "dir": "quick-xml",       "lang": "Rust",   "lang_class": "rust",   "ops": ["dom_parse", "sax_parse", "serialize"]},
    {"name": "roxmltree",       "dir": "roxmltree",       "lang": "Rust",   "lang_class": "rust",   "ops": ["dom_parse"]},
    {"name": "System.Xml",      "dir": "system-xml",      "lang": "C#",     "lang_class": "csharp", "ops": ["dom_parse", "sax_parse", "xpath_query", "serialize"]},
    {"name": "encoding/xml",    "dir": "encoding-xml",    "lang": "Go",     "lang_class": "go",     "ops": ["dom_parse", "sax_parse", "serialize"]},
    {"name": "fast-xml-parser", "dir": "fast-xml-parser", "lang": "JS",     "lang_class": "js",     "ops": ["dom_parse", "serialize"]},
]

SHAPES = ["wide", "deep"]

DATA_DIR = "data"
RESULTS_DIR = "results"
REPORT_TEMPLATE = "report/index.html"
