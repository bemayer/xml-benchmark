use quick_xml::events::Event;
use quick_xml::reader::Reader;
use quick_xml::writer::Writer;
use std::env;
use std::fs;
use std::io::Cursor;
use std::time::Instant;

fn bench_dom_parse(xml: &[u8], iterations: usize) -> f64 {
    let start = Instant::now();
    for _ in 0..iterations {
        let mut reader = Reader::from_reader(xml);
        let mut buf = Vec::new();
        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Eof) => break,
                Err(e) => { eprintln!("Error: {e}"); break; }
                _ => {}
            }
            buf.clear();
        }
    }
    start.elapsed().as_secs_f64() * 1000.0 / iterations as f64
}

fn bench_sax_parse(xml: &[u8], iterations: usize) -> f64 {
    bench_dom_parse(xml, iterations)
}

fn bench_serialize(xml: &[u8], iterations: usize) -> f64 {
    let mut events = Vec::new();
    let mut reader = Reader::from_reader(xml);
    let mut buf = Vec::new();
    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Eof) => break,
            Ok(e) => events.push(e.into_owned()),
            Err(_) => break,
        }
        buf.clear();
    }
    let start = Instant::now();
    for _ in 0..iterations {
        let mut writer = Writer::new(Cursor::new(Vec::new()));
        for event in &events {
            writer.write_event(event.clone()).ok();
        }
        let _ = writer.into_inner().into_inner().len();
    }
    start.elapsed().as_secs_f64() * 1000.0 / iterations as f64
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 { return; }
    let op = &args[1];
    let file = &args[2];
    let iterations: usize = args[3].parse().unwrap();
    let xml = fs::read(file).unwrap();

    match op.as_str() {
        "dom_parse" => {
            let ms = bench_dom_parse(&xml, iterations);
            println!("{{\"library\":\"quick-xml\",\"language\":\"Rust\",\"operation\":\"dom_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:.3}}}");
        }
        "sax_parse" => {
            let ms = bench_sax_parse(&xml, iterations);
            println!("{{\"library\":\"quick-xml\",\"language\":\"Rust\",\"operation\":\"sax_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:.3}}}");
        }
        "serialize" => {
            let ms = bench_serialize(&xml, iterations);
            println!("{{\"library\":\"quick-xml\",\"language\":\"Rust\",\"operation\":\"serialize\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:.3}}}");
        }
        _ => {
            println!("{{\"skipped\":true,\"operation\":\"{op}\",\"library\":\"quick-xml\"}}");
        }
    }
}
