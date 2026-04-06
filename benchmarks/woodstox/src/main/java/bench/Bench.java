package bench;

import com.ctc.wstx.stax.WstxInputFactory;
import javax.xml.stream.*;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;

public class Bench {
    public static void main(String[] args) throws Exception {
        if (args.length < 3) return;
        String op = args[0], file = args[1];
        int iterations = Integer.parseInt(args[2]);
        byte[] xml = Files.readAllBytes(Path.of(file));

        if (op.equals("sax_parse")) {
            WstxInputFactory factory = new WstxInputFactory();
            for (int i = 0; i < Math.min(5, iterations); i++) {
                XMLStreamReader reader = factory.createXMLStreamReader(new ByteArrayInputStream(xml));
                while (reader.hasNext()) reader.next();
                reader.close();
            }
            long start = System.nanoTime();
            for (int i = 0; i < iterations; i++) {
                XMLStreamReader reader = factory.createXMLStreamReader(new ByteArrayInputStream(xml));
                while (reader.hasNext()) reader.next();
                reader.close();
            }
            double ms = (System.nanoTime() - start) / 1e6 / iterations;
            System.out.printf("{\"library\":\"Woodstox\",\"language\":\"Java\",\"operation\":\"sax_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
        } else {
            System.out.printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"Woodstox\"}%n", op);
        }
    }
}
