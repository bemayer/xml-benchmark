use std::env;
use std::fs;
use std::time::Instant;

fn bench_dom_parse(xml: &str, iterations: usize) -> f64 {
    let start = Instant::now();
    for _ in 0..iterations {
        let _ = roxmltree::Document::parse(xml).unwrap();
    }
    start.elapsed().as_secs_f64() * 1000.0 / iterations as f64
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 { return; }
    let op = &args[1];
    let file = &args[2];
    let iterations: usize = args[3].parse().unwrap();
    let xml = fs::read_to_string(file).unwrap();

    match op.as_str() {
        "dom_parse" => {
            let ms = bench_dom_parse(&xml, iterations);
            println!("{{\"library\":\"roxmltree\",\"language\":\"Rust\",\"operation\":\"dom_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:.3}}}");
        }
        _ => {
            println!("{{\"skipped\":true,\"operation\":\"{op}\",\"library\":\"roxmltree\"}}");
        }
    }
}
