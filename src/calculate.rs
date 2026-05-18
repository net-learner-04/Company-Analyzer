use crate::parse;

fn year(
    base: &Vec<(String, i64)>,
    other: &Vec<(String, i64)>,
    calc: fn(f64, f64) -> f64,
) -> Vec<(String, f64)> {
    let mut result = Vec::new();
    for (date, base_val) in base.iter() {
        if let Some((_, other_val)) = other.iter().find(|(d, _)| d == date) {
            let calculated = calc(*base_val as f64, *other_val as f64);
            result.push((date.clone(), calculated));
        }
    }
    result
}

// ----- 수익성 지표 -----
fn roe(net_income: &Vec<(String, i64)>, equity: &Vec<(String, i64)>) -> Vec<(String, f64)> {
    year(net_income, equity, |ni, eq| ni / eq * 100.0)
}
fn roa(net_income: &Vec<(String, i64)>, assets: &Vec<(String, i64)>) -> Vec<(String, f64)> {
    year(net_income, assets, |ni, ast| ni / ast * 100.0)
}
fn opm(operating_income: &Vec<(String, i64)>, revenues: &Vec<(String, i64)>) -> Vec<(String, f64)> {
    year(operating_income, revenues, |oi, rv| oi / rv * 100.0)
}
fn npm(net_income: &Vec<(String, i64)>, revenues: &Vec<(String, i64)>) -> Vec<(String, f64)> {
    year(net_income, revenues, |ni, rv| ni / rv * 100.0)
}

// ----- 안정성 지표 -----
fn der(liabilities: &Vec<(String, i64)>, equity: &Vec<(String, i64)>) -> Vec<(String, f64)> {
    year(liabilities, equity, |ll, eq| ll / eq * 100.0)
}
fn er(equity: &Vec<(String, i64)>, assets: &Vec<(String, i64)>) -> Vec<(String, f64)> {
    year(equity, assets, |eq, ast| eq / ast * 100.0)
}
fn at(revenues: &Vec<(String, i64)>, assets: &Vec<(String, i64)>) -> Vec<(String, f64)> {
    year(revenues, assets, |rv, ast| rv / ast)
}

pub fn print(ticker: &str, data: parse::Data) {
    let roe_val = roe(&data.netincomeloss, &data.stockholdersequity);
    let roa_val = roa(&data.netincomeloss, &data.assets);
    let opm_val = opm(&data.operatingincomeloss, &data.revenues);
    let npm_val = npm(&data.netincomeloss, &data.revenues);
    let der_val = der(&data.liabilities, &data.stockholdersequity);
    let er_val  = er(&data.stockholdersequity, &data.assets);
    let at_val  = at(&data.revenues, &data.assets);

    let years: Vec<String> = roe_val.iter()
        .map(|(date, _)| date[..4].to_string())
        .collect();

    let year_header: String = years.iter()
        .map(|y| format!("{:>10}", y))
        .collect::<Vec<String>>()
        .join("");

    println!("=== {} Information ===", ticker);
    println!("{:>5}{}", "", year_header);
    println!("{:-<width$}", "", width = 5 + years.len() * 10);

    print!("{:<5}", "ROE:"); println!("{}", format_pct(&roe_val, &years));
    print!("{:<5}", "ROA:"); println!("{}", format_pct(&roa_val, &years));
    print!("{:<5}", "OPM:"); println!("{}", format_pct(&opm_val, &years));
    print!("{:<5}", "NPM:"); println!("{}", format_pct(&npm_val, &years));

    println!("{:-<width$}", "", width = 5 + years.len() * 10);

    print!("{:<5}", "DER:"); println!("{}", format_pct(&der_val, &years));
    print!("{:<5}", "ER:");  println!("{}", format_pct(&er_val, &years));
    print!("{:<5}", "AT:");  println!("{}", format_x(&at_val, &years));
}

fn format_pct(vals: &Vec<(String, f64)>, years: &Vec<String>) -> String {
    years.iter()
        .map(|y| vals.iter()
            .find(|(date, _)| date.starts_with(y))
            .map(|(_, v)| format!("{:>10.2}%", v))
            .unwrap_or_else(|| format!("{:>10}", "N/A")))
        .collect::<Vec<String>>()
        .join("")
}

fn format_x(vals: &Vec<(String, f64)>, years: &Vec<String>) -> String {
    years.iter()
        .map(|y| vals.iter()
            .find(|(date, _)| date.starts_with(y))
            .map(|(_, v)| format!("{:>10.2}x", v))
            .unwrap_or_else(|| format!("{:>10}", "N/A")))
        .collect::<Vec<String>>()
        .join("")
}
