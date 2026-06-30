import json, time, requests
from pathlib import Path


USER_AGENT = "company-analyzer pminseo2004@gmail.com"


def directory_path() -> Path:
    base = Path(__file__).resolve().parent
    path = base / "ca_json"
    return path


def ticker_file_path() -> Path:
    path = directory_path()
    path = path / "company-tickers.json"
    return path


def facts_file_path(ticker: str) -> Path:
    path = directory_path()
    path = path / f"{ticker}-facts.json"
    return path


def sic_file_path(ticker: str) -> Path:
    path = directory_path()
    path = path / f"{ticker}-sic.json"
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
        headers={"User-Agent": USER_AGENT},
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
        headers={"User-Agent": USER_AGENT},
    )
    json_file = response.text
    with open(facts_file_path(ticker), "w", encoding="utf-8") as f:
        f.write(json_file)


def get_company_sic(ticker: str, cik_ticker: str) -> str:
    directory_check()
    path = sic_file_path(ticker)

    if not duration_check(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            return cached.get("sicDescription", "")
        except (OSError, json.JSONDecodeError):
            pass

    try:
        response = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik_ticker}.json",
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        data = response.json()
        sic_desc = data.get("sicDescription", "")
    except (requests.RequestException, ValueError):
        sic_desc = ""

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"sicDescription": sic_desc}, f)
    except OSError:
        pass

    return sic_desc
