mod calculate;
mod extract;
mod parse;

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("Directions for Use: {} <ticker>", args[0]);
        eprintln!("Example: {} AAPL", args[0]);
        std::process::exit(1);
    }

    let ticker = args[1].to_uppercase();

    extract::get_company_tickers();

    let cik = extract::return_ticker(&ticker);

    if cik.is_empty() {
        eprintln!("Ticker cannot be found: {}", ticker);
        std::process::exit(1);
    }

    extract::get_company_facts(&ticker, &cik);

    let data = parse::Data::new(&ticker);

    calculate::print(&ticker, data);
}
