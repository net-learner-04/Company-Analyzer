use crate::parse;

// ----- 수익성 지표 -----

// 자기자본이익률
fn roe(net_income: Option<i64>, equity: Option<i64>) -> Option<f64> {
    match (net_income, equity) {
        (Some(ni), Some(eq)) => Some(ni as f64 / eq as f64 * 100.0),
        _ => None,
    }
}

// 총자산이익률
fn roa(net_income: Option<i64>, assets: Option<i64>) -> Option<f64> {
    match (net_income, assets) {
        (Some(ni), Some(ast)) => Some(ni as f64 / ast as f64 * 100.0),
        _ => None,
    }
}

// 영업이익률
fn opm(operating_income: Option<i64>, revenues: Option<i64>) -> Option<f64> {
    match (operating_income, revenues) {
        (Some(oi), Some(rv)) => Some(oi as f64 / rv as f64 * 100.0),
        _ => None,
    }
}

// 순이익률
fn npm(net_income: Option<i64>, revenues: Option<i64>) -> Option<f64> {
    match (net_income, revenues) {
        (Some(ni), Some(rv)) => Some(ni as f64 / rv as f64 * 100.0),
        _ => None,
    }
}

// ----- 안정성 지표 -----

// 부채비율
fn der(liabilities: Option<i64>, equity: Option<i64>) -> Option<f64> {
    match (liabilities, equity) {
        (Some(ll), Some(eq)) => Some(ll as f64 / eq as f64 * 100.0),
        _ => None,
    }
}

// 자기자본비율
fn er(equity: Option<i64>, assets: Option<i64>) -> Option<f64> {
    match (equity, assets) {
        (Some(eq), Some(ast)) => Some(eq as f64 / ast as f64 * 100.0),
        _ => None,
    }
}

// 총자산회전율
fn at(revenues: Option<i64>, assets: Option<i64>) -> Option<f64> {
    match (revenues, assets) {
        (Some(rv), Some(ast)) => Some(rv as f64 / ast as f64),
        _ => None,
    }
}

fn format(val: Option<f64>) -> String {
    match val {
        Some(v) => format!("{:.2}%", v),
        None => "N/A".to_string(),
    }
} 

pub fn print(ticker: &str, data: parse::Data) {
    let roe_val = roe(data.netincomeloss, data.stockholdersequity);
    let roa_val = roa(data.netincomeloss, data.assets);
    let opm_val = opm(data.operatingincomeloss, data.revenues);
    let npm_val = npm(data.netincomeloss, data.revenues);
    let der_val = der(data.liabilities, data.stockholdersequity);
    let er_val  = er(data.stockholdersequity, data.assets);
    let at_val  = at(data.revenues, data.assets);

    println!("=== {} Information ===", ticker);
    println!("ROE:        {}", format(roe_val));
    println!("ROA:        {}", format(roa_val));
    println!("OPM:        {}", format(opm_val));
    println!("NPM:        {}", format(npm_val));
    println!("DER:        {}", format(der_val));
    println!("ER:         {}", format(er_val));
    println!("AT:         {}", match at_val {
        Some(v) => format!("{:.?}x", v),
        None => "N/A".to_string(),
    });
}
