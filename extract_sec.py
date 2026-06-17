import json
import os
import time
from pathlib import Path
import requests


def directory_path() -> Path:
    env = os.environ.get("HOME")
    if env is None:
        raise RuntimeError("Failed to find home directory")
    path = Path(env)
    path = path / "ca_json"
    return path


def ticker_file_path() -> Path:
    path = directory_path()
    path = path / "company-tickers.json"
    return path


def facts_file_path(ticker: str) -> Path:
    path = directory_path()
    path = path / f"{ticker}-facts.json"
    return path


def directory_check():
    if not directory_path().exists():
        directory_path().mkdir(parents=True, exist_ok=True)


def duration_check(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        modified = path.stat().st_mtime
        elapsed = time.time() - modified
        return elapsed >= 24 * 60 * 60
    except OSError:
        return True


def get_company_tickers():
    directory_check()
    if not duration_check(ticker_file_path()):
        return
    response = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers={"User-Agent": "company-analyzer pminseo2004@gmail.com"},
    )
    json_file = response.text 
    with open(ticker_file_path(), "w", encoding="utf-8") as f:
        f.write(json_file)


def return_ticker(tkr: str) -> str:
    with open(ticker_file_path(), "r", encoding="utf-8") as f:
        file = f.read()
    cik_str = ""
    json_file = json.loads(file)
    for value in json_file.values():
        if value.get("ticker") == tkr:
            cik_str = f"{int(value['cik_str']):010d}"
            break
    return cik_str


def get_company_facts(ticker: str, cik_ticker: str):
    directory_check()
    if not duration_check(facts_file_path(ticker)):
        return
    response = requests.get(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_ticker}.json",
        headers={"User-Agent": "company-analyzer pminseo2004@gmail.com"},
    )
    json_file = response.text
    with open(facts_file_path(ticker), "w", encoding="utf-8") as f:
        f.write(json_file) 
