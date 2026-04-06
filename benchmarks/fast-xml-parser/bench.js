const fs = require("fs");
const { XMLParser, XMLBuilder } = require("fast-xml-parser");

const op = process.argv[2];
const file = process.argv[3];
const iterations = parseInt(process.argv[4], 10);
const xml = fs.readFileSync(file, "utf-8");

if (op === "dom_parse") {
  const parser = new XMLParser({ ignoreAttributes: false });
  for (let i = 0; i < Math.min(5, iterations); i++) parser.parse(xml);
  const start = process.hrtime.bigint();
  for (let i = 0; i < iterations; i++) parser.parse(xml);
  const ms = Number(process.hrtime.bigint() - start) / 1e6 / iterations;
  console.log(JSON.stringify({ library: "fast-xml-parser", language: "JS", operation: "dom_parse", file, iterations, time_ms: +ms.toFixed(3) }));
} else if (op === "serialize") {
  const parser = new XMLParser({ ignoreAttributes: false });
  const obj = parser.parse(xml);
  const builder = new XMLBuilder({ ignoreAttributes: false });
  for (let i = 0; i < Math.min(5, iterations); i++) builder.build(obj);
  const start = process.hrtime.bigint();
  for (let i = 0; i < iterations; i++) builder.build(obj);
  const ms = Number(process.hrtime.bigint() - start) / 1e6 / iterations;
  console.log(JSON.stringify({ library: "fast-xml-parser", language: "JS", operation: "serialize", file, iterations, time_ms: +ms.toFixed(3) }));
} else {
  console.log(JSON.stringify({ skipped: true, operation: op, library: "fast-xml-parser" }));
}
