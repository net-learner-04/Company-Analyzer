use crate::parse;

fn year(
    base: &[(String, i64)],
    other: &[(String, i64)],
    calc: fn(f64, f64) -> f64,
) -> Vec<(String, f64)> {
    let mut result = Vec::new();
    for (date, base_val) in base.iter() {
        if date.len() < 4 {
            continue;
        }
        let base_yr = &date[..4];

        if let Some((_, other_val)) = other
            .iter()
            .find(|(d, _)| d.len() >= 4 && &d[..4] == base_yr)
        {
            let calculated = calc(*base_val as f64, *other_val as f64);
            result.push((base_yr.to_string(), calculated));
        }
    }
    result
}

fn roe(net_income: &[(String, i64)], equity: &[(String, i64)]) -> Vec<(String, f64)> {
    year(net_income, equity, |ni, eq| {
        if eq == 0.0 { 0.0 } else { ni / eq * 100.0 }
    })
}
fn roa(net_income: &[(String, i64)], assets: &[(String, i64)]) -> Vec<(String, f64)> {
    year(net_income, assets, |ni, ast| {
        if ast == 0.0 { 0.0 } else { ni / ast * 100.0 }
    })
}
fn opm(operating_income: &[(String, i64)], revenues: &[(String, i64)]) -> Vec<(String, f64)> {
    year(operating_income, revenues, |oi, rv| {
        if rv == 0.0 { 0.0 } else { oi / rv * 100.0 }
    })
}
fn npm(net_income: &[(String, i64)], revenues: &[(String, i64)]) -> Vec<(String, f64)> {
    year(net_income, revenues, |ni, rv| {
        if rv == 0.0 { 0.0 } else { ni / rv * 100.0 }
    })
}

fn der(liabilities: &[(String, i64)], equity: &[(String, i64)]) -> Vec<(String, f64)> {
    year(liabilities, equity, |ll, eq| {
        if eq == 0.0 { 0.0 } else { ll / eq * 100.0 }
    })
}
fn er(equity: &[(String, i64)], assets: &[(String, i64)]) -> Vec<(String, f64)> {
    year(equity, assets, |eq, ast| {
        if ast == 0.0 { 0.0 } else { eq / ast * 100.0 }
    })
}
fn at(revenues: &[(String, i64)], assets: &[(String, i64)]) -> Vec<(String, f64)> {
    year(
        revenues,
        assets,
        |rv, ast| if ast == 0.0 { 0.0 } else { rv / ast },
    )
}

pub fn print(ticker: &str, data: parse::Data) {
    let roe_val = roe(&data.netincomeloss, &data.stockholdersequity);
    let roa_val = roa(&data.netincomeloss, &data.assets);
    let opm_val = opm(&data.operatingincomeloss, &data.revenues);
    let npm_val = npm(&data.netincomeloss, &data.revenues);
    let der_val = der(&data.liabilities, &data.stockholdersequity);
    let er_val = er(&data.stockholdersequity, &data.assets);
    let at_val = at(&data.revenues, &data.assets);

    let mut year_set = Vec::new();
    let all_datasets = [
        &roe_val, &roa_val, &opm_val, &npm_val, &der_val, &er_val, &at_val,
    ];

    for dataset in all_datasets.iter() {
        for (yr, _) in dataset.iter() {
            year_set.push(yr.clone());
        }
    }

    year_set.sort();
    year_set.dedup();

    let years = year_set;

    if years.is_empty() {
        println!("=== {} Information ===", ticker);
        println!("  No valid financial data to display.");
        return;
    }

    let year_header: String = years
        .iter()
        .map(|y| format!("{:>10}", y))
        .collect::<Vec<String>>()
        .join("");

    println!("\t\t=== {} Information ===", ticker);
    println!("{:>5}{}", "", year_header);
    println!("{:-<width$}", "", width = 5 + years.len() * 10);

    print!("{:<5}", "ROE:");
    println!("{}", format_pct(&roe_val, &years));
    print!("{:<5}", "ROA:");
    println!("{}", format_pct(&roa_val, &years));
    print!("{:<5}", "OPM:");
    println!("{}", format_pct(&opm_val, &years));
    print!("{:<5}", "NPM:");
    println!("{}", format_pct(&npm_val, &years));

    println!("{:-<width$}", "", width = 5 + years.len() * 10);

    print!("{:<5}", "DER:");
    println!("{}", format_pct(&der_val, &years));
    print!("{:<5}", "ER:");
    println!("{}", format_pct(&er_val, &years));
    print!("{:<5}", "AT:");
    println!("{}", format_x(&at_val, &years));
}

fn format_pct(vals: &[(String, f64)], years: &[String]) -> String {
    years
        .iter()
        .map(|y| {
            vals.iter()
                .find(|(date, _)| date == y)
                .map(|(_, v)| format!("{:>10.2}%", v))
                .unwrap_or_else(|| format!("{:>10}", "N/A"))
        })
        .collect::<Vec<String>>()
        .join("")
}

fn format_x(vals: &[(String, f64)], years: &[String]) -> String {
    years
        .iter()
        .map(|y| {
            vals.iter()
                .find(|(date, _)| date == y)
                .map(|(_, v)| format!("{:>10.2}x", v))
                .unwrap_or_else(|| format!("{:>10}", "N/A"))
        })
        .collect::<Vec<String>>()
        .join("")
}
