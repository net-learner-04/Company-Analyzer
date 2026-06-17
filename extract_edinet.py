import io
import json
import os
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

import parse


def ca_dir() -> Path:
    p = Path(os.environ.get("HOME") or "")
    if not os.environ.get("HOME"):
        raise RuntimeError("HOME not set")
    p = p / "ca_json"
    return p


def ensure_dir():
    d = ca_dir()
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)


def index_path(sec: str) -> Path:
    p = ca_dir()
    p = p / f"{sec}-edinet-index.json"
    return p


def facts_path(sec: str) -> Path:
    p = ca_dir()
    p = p / f"{sec}-edinet-facts.json"
    return p


def stale(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        modified = path.stat().st_mtime
        elapsed = time.time() - modified
        return elapsed >= 86400
    except OSError:
        return True


def api_key() -> str:
    key = os.environ.get("EDINET_API_KEY")
    if key is None:
        print("[오류] EDINET_API_KEY 환경변수를 설정해주세요.", file=sys.stderr)
        print("  발급 : https://api.edinet-fsa.go.jp/", file=sys.stderr)
        print("  설정 : export EDINET_API_KEY=<key>", file=sys.stderr)
        sys.exit(1)
    return key


def ts_to_date(ts: int) -> str:
    d = ts // 86400
    z = d + 719468
    era = z // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    day = doy - (153 * mp + 2) // 5 + 1
    mon = mp + 3 if mp < 10 else mp - 9
    yr = y + 1 if mon <= 2 else y
    return f"{yr:04d}-{mon:02d}-{day:02d}"


def date_ago(n: int) -> str:
    now = int(time.time())
    return ts_to_date(max(now - n * 86400, 0))


def fetch_day(session: requests.Session, date: str, key: str) -> list:
    url = (
        f"https://api.edinet-fsa.go.jp/api/v2/documents.json"
        f"?date={date}&type=2&Subscription-Key={key}"
    )
    try:
        r = session.get(url, timeout=15)
        if r.status_code // 100 == 2:
            v = r.json()
            return v.get("results") or []
    except (requests.RequestException, ValueError):
        pass
    return []


def find_reports(session: requests.Session, sec: str, key: str) -> list:
    idx = index_path(sec)
    if not stale(idx):
        try:
            with open(idx, "r", encoding="utf-8") as f:
                v = json.load(f)
            if isinstance(v, list) and v:
                return [tuple(item) for item in v]
        except (OSError, json.JSONDecodeError):
            pass

    sec5 = f"{sec}0"
    found = []

    print(f"[EDINET] {sec} 연간보고서 검색", end="", file=sys.stderr)

    for day in range(500):
        if day % 60 == 59:
            print(".", end="", file=sys.stderr)
        for doc in fetch_day(session, date_ago(day), key):
            if doc.get("formCode") != "030000":
                continue
            sc = doc.get("secCode") or ""
            if sc != sec5 and sc != sec:
                continue
            doc_id = doc.get("docID") or ""
            end = doc.get("periodEnd") or ""
            if not doc_id or len(end) < 4:
                continue
            yr = end[:4]
            if not any(e.startswith(yr) for _, e in found):
                found.append((doc_id, end))
        if len(found) >= 5:
            break
        time.sleep(0.06)

    print(f" {len(found)}건", file=sys.stderr)
    found.sort(key=lambda x: x[1], reverse=True)
    found = found[:5]

    try:
        with open(idx, "w", encoding="utf-8") as f:
            json.dump(found, f)
    except OSError:
        pass
    return found


def download_zip(session: requests.Session, doc_id: str, key: str):
    url = (
        f"https://api.edinet-fsa.go.jp/api/v2/documents/{doc_id}"
        f"?type=5&Subscription-Key={key}"
    )
    try:
        r = session.get(url, timeout=60)
        if r.status_code // 100 != 2:
            return None
        return r.content
    except requests.RequestException:
        return None


def xbrl_from_zip(byte_data: bytes):
    try:
        arc = zipfile.ZipFile(io.BytesIO(byte_data))
    except zipfile.BadZipFile:
        return None

    best_name = None
    best_sz = 0
    best_pri = False

    for info in arc.infolist():
        name = info.filename.lower()
        if not name.endswith(".xbrl"):
            continue
        sz = info.file_size
        pri = "asr" in name or "030000" in name
        if (pri and not best_pri) or (pri == best_pri and sz > best_sz):
            best_name = info.filename
            best_sz = sz
            best_pri = pri

    if best_name is None:
        return None

    raw = arc.read(best_name)
    return raw.decode("utf-8", errors="replace")


REV = ["NetSales", 
       "NetSalesAndRevenues", 
       "Revenue",
        "Revenues",
        "NetSalesSummaryOfBusinessResults"]

OPE = ["OperatingIncome", 
       "OperatingProfit", 
       "OperatingProfitLoss", 
       "OperatingIncomeLoss"]

NET = [
    "ProfitAttributableToOwnersOfParent",
    "ProfitLossAttributableToOwnersOfParent",
    "NetIncome",
    "NetIncomeLoss",
    "ProfitLoss"]

AST = ["Assets", 
       "TotalAssets"]

LIA = ["Liabilities", 
       "TotalLiabilities"]

EQT = ["EquityAttributableToOwnersOfParent", 
       "NetAssets", 
       "TotalNetAssets", 
       "StockholdersEquity"]


def is_target(n: str) -> bool:
    return any(n in tags for tags in (REV, OPE, NET, AST, LIA, EQT))


def ctx_score(c: str) -> int:
    c = c.lower()
    s = 0
    if "currentyear" in c:
        s += 100
    if "consolidated" in c:
        s += 30
    if "prior" in c or "previous" in c:
        s -= 300
    if "nonconsolidated" in c or "individual" in c:
        s -= 100
    if "segment" in c:
        s -= 50
    return s


def apply_scale(raw: int, dec: int) -> int:
    e = -dec
    e = max(-18, min(18, e))
    if e > 0:
        return raw * (10 ** e)
    if e < 0:
        divisor = 10 ** (-e)
        q = abs(raw) // divisor
        return -q if raw < 0 else q
    return raw


def parse_xbrl(xml: str) -> dict:
    data: dict = {}
    try:
        events = ET.iterparse(io.StringIO(xml), events=("end",))
    except ET.ParseError:
        return data

    for _, elem in events:
        tag = elem.tag
        local = tag.split("}", 1)[1] if "}" in tag else tag
        if not is_target(local):
            continue

        ctx = ""
        dec = 0
        nil = False
        for k, v in elem.attrib.items():
            key_local = k.split("}", 1)[1] if "}" in k else k
            if key_local == "contextRef":
                ctx = v
            elif key_local == "decimals":
                try:
                    dec = int(v)
                except ValueError:
                    dec = 0
            elif key_local == "nil":
                nil = v == "true"

        if nil or not ctx:
            continue

        text = (elem.text or "").strip()
        if not text:
            continue
        try:
            raw = int(text)
        except ValueError:
            continue

        data.setdefault(local, []).append((ctx, apply_scale(raw, dec)))

    return data


def pick(data: dict, tags: list):
    best = None
    best_score = None
    for t in tags:
        for ctx, val in data.get(t, []):
            score = ctx_score(ctx)
            if best_score is None or score > best_score:
                best_score = score
                best = val
    return best


def xbrl_to_row(xml: str):
    d = parse_xbrl(xml)
    rev = pick(d, REV)
    if rev is None:
        return None
    return [
        rev,
        pick(d, OPE) or 0,
        pick(d, NET) or 0,
        pick(d, AST) or 0,
        pick(d, LIA) or 0,
        pick(d, EQT) or 0,
    ]


def save_cache(data: "parse.Data", path: Path):
    v = {
        "revenues": data.revenues,
        "operatingincomeloss": data.operatingincomeloss,
        "netincomeloss": data.netincomeloss,
        "assets": data.assets,
        "liabilities": data.liabilities,
        "stockholdersequity": data.stockholdersequity,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(v, f)
    except OSError:
        pass


def load_cache(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            v = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    def to_vec(arr):
        result = []
        for item in arr or []:
            try:
                result.append((item[0], int(item[1])))
            except (IndexError, TypeError, ValueError):
                continue
        return result

    return parse.Data(
        revenues=to_vec(v.get("revenues")),
        operatingincomeloss=to_vec(v.get("operatingincomeloss")),
        netincomeloss=to_vec(v.get("netincomeloss")),
        assets=to_vec(v.get("assets")),
        liabilities=to_vec(v.get("liabilities")),
        stockholdersequity=to_vec(v.get("stockholdersequity")),
    )


def get_data(sec_code: str) -> "parse.Data":
    ensure_dir()
    key = api_key()
    session = requests.Session()
    cache = facts_path(sec_code)

    if not stale(cache):
        d = load_cache(cache)
        if d is not None:
            return d

    reports = find_reports(session, sec_code, key)
    if not reports:
        print(f"[EDINET] 증권코드 {sec_code}의 연간리포트를 찾을 수 없습니다.", file=sys.stderr)
        return parse.Data(
            revenues=[],
            operatingincomeloss=[],
            netincomeloss=[],
            assets=[],
            liabilities=[],
            stockholdersequity=[],
        )

    rev, ope, net, ast, lia, eqt = [], [], [], [], [], []

    for doc_id, period_end in reports:
        print(f"[EDINET] {period_end} 획득 중...", end="", file=sys.stderr)
        zip_bytes = download_zip(session, doc_id, key)
        if zip_bytes is None:
            print(" 다운로드 실패", file=sys.stderr)
            continue
        xbrl = xbrl_from_zip(zip_bytes)
        if xbrl is None:
            print(" XBRL 추출 실패", file=sys.stderr)
            continue
        row = xbrl_to_row(xbrl)
        if row is None:
            print(" 파싱 실패", file=sys.stderr)
            continue
        print(" 완료", file=sys.stderr)

        r, o, n, a, l, e = row
        e = (a - l) if (e == 0 and a > 0) else e
        rev.append((period_end, r))
        ope.append((period_end, o))
        net.append((period_end, n))
        ast.append((period_end, a))
        lia.append((period_end, l))
        eqt.append((period_end, e))

        time.sleep(0.3)

    for v in (rev, ope, net, ast, lia, eqt):
        v.sort(key=lambda x: x[0], reverse=True)

    data = parse.Data(
        revenues=rev,
        operatingincomeloss=ope,
        netincomeloss=net,
        assets=ast,
        liabilities=lia,
        stockholdersequity=eqt,
    )
    save_cache(data, cache)
    return data
