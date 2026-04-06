package bench;

import com.ximpleware.*;
import java.nio.file.Files;
import java.nio.file.Path;

public class Bench {
    public static void main(String[] args) throws Exception {
        if (args.length < 3) { System.err.println("Usage: bench <op> <file> <iterations>"); return; }
        String op = args[0], file = args[1];
        int iterations = Integer.parseInt(args[2]);
        byte[] xml = Files.readAllBytes(Path.of(file));

        if (op.equals("dom_parse")) {
            for (int i = 0; i < Math.min(5, iterations); i++) {
                VTDGen vg = new VTDGen(); vg.setDoc(xml.clone()); vg.parse(false);
            }
            long start = System.nanoTime();
            for (int i = 0; i < iterations; i++) {
                VTDGen vg = new VTDGen(); vg.setDoc(xml.clone()); vg.parse(false);
            }
            double ms = (System.nanoTime() - start) / 1e6 / iterations;
            System.out.printf("{\"library\":\"VTD-XML\",\"language\":\"Java\",\"operation\":\"dom_parse\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
        } else if (op.equals("xpath_query")) {
            VTDGen vg = new VTDGen(); vg.setDoc(xml.clone()); vg.parse(false);
            VTDNav vn = vg.getNav();
            for (int i = 0; i < Math.min(5, iterations); i++) {
                AutoPilot ap = new AutoPilot(vn); ap.selectXPath("//*[@id]");
                int count = 0; while (ap.evalXPath() != -1) count++;
                vn.toElement(VTDNav.ROOT);
            }
            long start = System.nanoTime();
            for (int i = 0; i < iterations; i++) {
                AutoPilot ap = new AutoPilot(vn); ap.selectXPath("//*[@id]");
                int count = 0; while (ap.evalXPath() != -1) count++;
                vn.toElement(VTDNav.ROOT);
            }
            double ms = (System.nanoTime() - start) / 1e6 / iterations;
            System.out.printf("{\"library\":\"VTD-XML\",\"language\":\"Java\",\"operation\":\"xpath_query\",\"file\":\"%s\",\"iterations\":%d,\"time_ms\":%.3f}%n", file, iterations, ms);
        } else {
            System.out.printf("{\"skipped\":true,\"operation\":\"%s\",\"library\":\"VTD-XML\"}%n", op);
        }
    }
}
