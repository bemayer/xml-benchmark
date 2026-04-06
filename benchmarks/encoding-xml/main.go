package main

import (
	"bytes"
	"encoding/xml"
	"fmt"
	"io"
	"os"
	"strconv"
	"time"
)

func benchDOMParse(data []byte, iterations int) float64 {
	start := time.Now()
	for i := 0; i < iterations; i++ {
		var root interface{}
		xml.Unmarshal(data, &root)
	}
	return float64(time.Since(start).Microseconds()) / float64(iterations) / 1000.0
}

func benchSAXParse(data []byte, iterations int) float64 {
	start := time.Now()
	for i := 0; i < iterations; i++ {
		decoder := xml.NewDecoder(bytes.NewReader(data))
		for {
			_, err := decoder.Token()
			if err == io.EOF { break }
			if err != nil { break }
		}
	}
	return float64(time.Since(start).Microseconds()) / float64(iterations) / 1000.0
}

func benchSerialize(data []byte, iterations int) float64 {
	type Node struct {
		XMLName  xml.Name
		Attrs    []xml.Attr `xml:",any,attr"`
		Content  []byte     `xml:",chardata"`
		Children []Node     `xml:",any"`
	}
	var root Node
	xml.Unmarshal(data, &root)
	start := time.Now()
	for i := 0; i < iterations; i++ {
		xml.Marshal(root)
	}
	return float64(time.Since(start).Microseconds()) / float64(iterations) / 1000.0
}

func main() {
	if len(os.Args) < 4 { return }
	op := os.Args[1]
	file := os.Args[2]
	iterations, _ := strconv.Atoi(os.Args[3])
	data, _ := os.ReadFile(file)

	switch op {
	case "dom_parse":
		ms := benchDOMParse(data, iterations)
		fmt.Printf("{\"library\":\"encoding/xml\",\"language\":\"Go\",\"operation\":\"dom_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", file, iterations, ms)
	case "sax_parse":
		ms := benchSAXParse(data, iterations)
		fmt.Printf("{\"library\":\"encoding/xml\",\"language\":\"Go\",\"operation\":\"sax_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", file, iterations, ms)
	case "serialize":
		ms := benchSerialize(data, iterations)
		fmt.Printf("{\"library\":\"encoding/xml\",\"language\":\"Go\",\"operation\":\"serialize\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}\n", file, iterations, ms)
	default:
		fmt.Printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"encoding/xml\"}\n", op)
	}
}
