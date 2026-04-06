package bench;

import javax.xml.parsers.*;
import javax.xml.xpath.*;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.*;
import org.xml.sax.*;
import org.xml.sax.helpers.DefaultHandler;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;

public class Bench {
    public static void main(String[] args) throws Exception {
        if (args.length < 3) return;
        String op = args[0], file = args[1];
        int iterations = Integer.parseInt(args[2]);
        byte[] xml = Files.readAllBytes(Path.of(file));

        switch (op) {
            case "dom_parse" -> {
                DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
                for (int i = 0; i < Math.min(5, iterations); i++) { DocumentBuilder db = dbf.newDocumentBuilder(); db.parse(new ByteArrayInputStream(xml)); }
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) { DocumentBuilder db = dbf.newDocumentBuilder(); db.parse(new ByteArrayInputStream(xml)); }
                double ms = (System.nanoTime() - start) / 1e6 / iterations;
                System.out.printf("{\"library\":\"Xerces\",\"language\":\"Java\",\"operation\":\"dom_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
            }
            case "sax_parse" -> {
                SAXParserFactory spf = SAXParserFactory.newInstance();
                DefaultHandler handler = new DefaultHandler();
                for (int i = 0; i < Math.min(5, iterations); i++) { SAXParser sp = spf.newSAXParser(); sp.parse(new ByteArrayInputStream(xml), handler); }
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) { SAXParser sp = spf.newSAXParser(); sp.parse(new ByteArrayInputStream(xml), handler); }
                double ms = (System.nanoTime() - start) / 1e6 / iterations;
                System.out.printf("{\"library\":\"Xerces\",\"language\":\"Java\",\"operation\":\"sax_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
            }
            case "xpath_query" -> {
                DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
                DocumentBuilder db = dbf.newDocumentBuilder();
                Document doc = db.parse(new ByteArrayInputStream(xml));
                XPathFactory xpf = XPathFactory.newInstance();
                for (int i = 0; i < Math.min(5, iterations); i++) { XPath xp = xpf.newXPath(); NodeList nl = (NodeList) xp.evaluate("//*[@id]", doc, XPathConstants.NODESET); }
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) { XPath xp = xpf.newXPath(); NodeList nl = (NodeList) xp.evaluate("//*[@id]", doc, XPathConstants.NODESET); int dummy = nl.getLength(); }
                double ms = (System.nanoTime() - start) / 1e6 / iterations;
                System.out.printf("{\"library\":\"Xerces\",\"language\":\"Java\",\"operation\":\"xpath_query\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
            }
            case "serialize" -> {
                DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
                DocumentBuilder db = dbf.newDocumentBuilder();
                Document doc = db.parse(new ByteArrayInputStream(xml));
                TransformerFactory tf = TransformerFactory.newInstance();
                for (int i = 0; i < Math.min(5, iterations); i++) { Transformer t = tf.newTransformer(); StringWriter sw = new StringWriter(); t.transform(new DOMSource(doc), new StreamResult(sw)); }
                long start = System.nanoTime();
                for (int i = 0; i < iterations; i++) { Transformer t = tf.newTransformer(); StringWriter sw = new StringWriter(); t.transform(new DOMSource(doc), new StreamResult(sw)); }
                double ms = (System.nanoTime() - start) / 1e6 / iterations;
                System.out.printf("{\"library\":\"Xerces\",\"language\":\"Java\",\"operation\":\"serialize\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
            }
            default -> System.out.printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"Xerces\"}%n", op);
        }
    }
}
