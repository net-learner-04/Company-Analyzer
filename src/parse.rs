use crate::extract;
use serde_json;
use std::fs;

pub struct Data {
    pub netincomeloss: Option<i64>,        // 순이익
    pub assets: Option<i64>,              // 총자산
    pub stockholdersequity: Option<i64>,  //자기자본
    pub revenues: Option<i64>,            // 매출
    pub operatingincomeloss: Option<i64>, // 영업이익
    pub liabilities: Option<i64>,         // 부채
}

fn extract_latest(json: &serde_json::Value, key: &str) -> Option<i64> {
    let arr = json["facts"]["us-gaap"][key]["units"]["USD"].as_array()?;
    arr.iter()
        .filter(|item| item["form"].as_str() == Some("10-K") && item["fp"].as_str() == Some("FY"))
        .max_by_key(|item| item["end"].as_str().unwrap_or(""))
        .and_then(|item| item["val"].as_i64())
}

impl Data {
    pub fn new(ticker: &str) -> Data {
        let path = extract::facts_file_path(ticker);
        let content = fs::read_to_string(path).unwrap();
        let json: serde_json::Value = serde_json::from_str(&content).unwrap();

        let info = Data {
            netincomeloss: extract_latest(&json, "NetIncomeLoss"),
            assets: extract_latest(&json, "Assets"),
            stockholdersequity: extract_latest(&json, "StockholdersEquity"),
            revenues: extract_latest(&json, "Revenues")
                .or_else(|| extract_latest(&json, "RevenueFromContractWithCustomerExcludingAssessedTax")),
            operatingincomeloss: extract_latest(&json, "OperatingIncomeLoss"),
            liabilities: extract_latest(&json, "Liabilities"),
        };

        info
    }
}
