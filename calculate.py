import unicodedata
from rich import box
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


METRICS = {
    "roe": dict(
        label="ROE (자기자본이익률)",
        desc="자기자본 대비 이익 창출 능력",
        # (기준치, 점수) 방식 - 예를 들어 roe 15 ~ 25 점이면 3점으로 책정. (단, der 처럼 낮을수록 좋은 지표는 그 반대임)
        points=[(0, 1), (8, 2), (15, 3), (25, 4)], default=5,
    ),
    "roa": dict(
        label="ROA (총자산이익률)",
        desc="총자산을 활용한 수익 창출 효율",
        points=[(0, 1), (2, 2), (8, 3), (15, 4)], default=5,
    ),
    "opm": dict(
        label="OPM (영업이익률)",
        desc="본업에서의 수익 창출력",
        points=[(0, 1), (5, 2), (15, 3), (25, 4)], default=5,
    ),
    "npm": dict(
        label="NPM (순이익률)",
        desc="매출 대비 최종적으로 남는 이익 비중",
        points=[(0, 1), (3, 2), (10, 3), (18, 4)], default=5,
    ),
    "er": dict(
        label="ER (자기자본비율)",
        desc="총자산 중 자기자본이 차지하는 비중, 높을수록 재무구조 안정",
        points=[(10, 1), (20, 2), (40, 3), (60, 4)], default=5,
    ),
    "der": dict(
        label="DER (부채자본비율)",
        desc="자기자본 대비 부채 의존도, 낮을수록 안정적",
        points=[(50, 5), (80, 4), (150, 3), (300, 2)], default=1,
    ),
    "dr": dict(
        label="DR (총부채비율)",
        desc="총자산 중 부채가 차지하는 비중, 낮을수록 안정적",
        points=[(40, 5), (50, 4), (70, 3), (80, 2)], default=1,
    ),
    "growth": dict(
        label="성장률",
        desc="매출 및 순이익의 전년 대비 증감 추세",
        points=[(-10, 1), (0, 2), (10, 3), (20, 4)], default=5,
    ),
}


def _disp_width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def _ljust(s: str, width: int) -> str:
    pad = max(0, width - _disp_width(s))
    return s + " " * pad


def match_years(base, other, calc):
    result = []
    for date, base_val in base:
        if len(date) < 4:
            continue
        yr = date[:4]
        match = next(
            (other_val for d, other_val in other if len(d) >= 4 and d[:4] == yr),
            None,
        )
        if match is not None:
            result.append((yr, calc(float(base_val), float(match))))
    return result


def roe(net_income, equity):
    """ROE 자기자본이익률"""
    return match_years(net_income, equity, lambda ni, eq: 0.0 if eq == 0.0 else ni / eq * 100.0)


def roa(net_income, assets):
    """ROA 총자산이익률"""
    return match_years(net_income, assets, lambda ni, ast: 0.0 if ast == 0.0 else ni / ast * 100.0)


def opm(op_income, revenues):
    """OPM 영업이익률"""
    return match_years(op_income, revenues, lambda oi, rv: 0.0 if rv == 0.0 else oi / rv * 100.0)


def npm(net_income, revenues):
    """NPM 순이익률"""
    return match_years(net_income, revenues, lambda ni, rv: 0.0 if rv == 0.0 else ni / rv * 100.0)


def der(liabilities, equity):
    """DER 부채자본비율"""
    return match_years(liabilities, equity, lambda ll, eq: 0.0 if eq == 0.0 else ll / eq * 100.0)


def er(equity, assets):
    """ER 자기자본비율"""
    return match_years(equity, assets, lambda eq, ast: 0.0 if ast == 0.0 else eq / ast * 100.0)


def at(revenues, assets):
    """AT 자산회전율"""
    return match_years(revenues, assets, lambda rv, ast: 0.0 if ast == 0.0 else rv / ast)


def debt_ratio(liabilities, assets):
    """DR 총부채비율"""
    return match_years(liabilities, assets, lambda ll, ast: 0.0 if ast == 0.0 else ll / ast * 100.0)


def equity_multiplier(assets, equity):
    """EM 재무레버리지"""
    return match_years(assets, equity, lambda ast, eq: 0.0 if eq == 0.0 else ast / eq)


def yoy_growth(vals):
    sorted_vals = sorted(vals, key=lambda x: x[0])

    by_year = []
    for date, val in sorted_vals:
        if len(date) < 4:
            continue
        yr = date[:4]
        if by_year and by_year[-1][0] == yr:
            by_year[-1] = (yr, val)
            continue
        by_year.append((yr, val))

    result = []
    for i in range(1, len(by_year)):
        yr, cur = by_year[i]
        _, prev = by_year[i - 1]
        growth = 0.0 if prev == 0 else (cur - prev) / abs(prev) * 100.0
        result.append((yr, growth))
    return result


def dupont(npm_vals, at_vals, em_vals):
    result = []
    for yr, npm_v in npm_vals:
        at_v = next((v for y, v in at_vals if y == yr), None)
        if at_v is None:
            continue
        em_v = next((v for y, v in em_vals if y == yr), None)
        if em_v is None:
            continue
        result.append((yr, npm_v / 100.0 * at_v * em_v * 100.0))
    return result


def fmt_val(v: int) -> str:
    s = str(abs(v))
    chunks = []
    for i in range(len(s), 0, -3):
        start = max(0, i - 3)
        chunks.append(s[start:i])
    chunked = ",".join(reversed(chunks))
    return f"-{chunked}" if v < 0 else chunked


def raw_cell(vals, year) -> Text:
    found = next(((d, v) for d, v in vals if len(d) >= 4 and d[:4] == year), None)
    text = fmt_val(found[1]) if found else "N/A"
    cell = Text(text, justify="right")
    if found and found[1] < 0:
        cell.stylize("red")
    return cell


def pct_cell(vals, year) -> Text:
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    text = f"{found[1]:.2f}%" if found else "N/A"
    cell = Text(text, justify="right")
    if found:
        if found[1] < 0.0:
            cell.stylize("red")
        elif found[1] >= 15.0:
            cell.stylize("green")
    return cell


def growth_cell(vals, year) -> Text:
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    text = f"{found[1]:+.2f}%" if found else "N/A"
    cell = Text(text, justify="right")
    if found:
        if found[1] < 0.0:
            cell.stylize("red")
        elif found[1] > 0.0:
            cell.stylize("green")
    return cell


def x_cell(vals, year) -> Text:
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    text = f"{found[1]:.2f}x" if found else "N/A"
    return Text(text, justify="right")


def label_cell(text: str) -> Text:
    cell = Text(text)
    cell.stylize("bold")
    return cell


def section_header_row(years, title) -> list:
    row = [label_cell(title)]
    for _ in years:
        row.append(Text(""))
    return row


def print_table(ticker: str, data):
    roe_val = roe(data.netincomeloss, data.stockholdersequity)
    roa_val = roa(data.netincomeloss, data.assets)
    opm_val = opm(data.operatingincomeloss, data.revenues)
    npm_val = npm(data.netincomeloss, data.revenues)
    der_val = der(data.liabilities, data.stockholdersequity)
    er_val = er(data.stockholdersequity, data.assets)
    at_val = at(data.revenues, data.assets)

    dr_val = debt_ratio(data.liabilities, data.assets)
    em_val = equity_multiplier(data.assets, data.stockholdersequity)

    rev_growth = yoy_growth(data.revenues)
    ni_growth = yoy_growth(data.netincomeloss)

    dupont_val = dupont(npm_val, at_val, em_val)

    years = []
    for ds in (
        data.revenues,
        data.netincomeloss,
        data.operatingincomeloss,
        data.assets,
        data.liabilities,
        data.stockholdersequity,
    ):
        for date, _ in ds:
            if len(date) >= 4:
                years.append(date[:4])
    for ds in (
        roe_val, roa_val, opm_val, npm_val,
        der_val, er_val, at_val,
        dr_val, em_val,
        rev_growth, ni_growth, dupont_val,
    ):
        for yr, _ in ds:
            years.append(yr)

    years = sorted(set(years))

    if not years:
        print(f"=== {ticker} ===")
        print("  표시할 재무 데이터가 없습니다.")
        return

    table = Table(box=box.ROUNDED, show_lines=False)
    table.add_column(f"  {ticker}  재무제표", header_style="bold green")
    for y in years:
        table.add_column(y, justify="center", header_style="bold")

    table.add_row(*section_header_row(years, "▸ 손익"))
    for label, vals in (
        ("매출", data.revenues),
        ("영업이익", data.operatingincomeloss),
        ("순이익", data.netincomeloss),
    ):
        table.add_row(label_cell(label), *[raw_cell(vals, y) for y in years])

    table.add_row(*section_header_row(years, "▸ 성장률"))
    table.add_row(label_cell("매출 성장률"), *[growth_cell(rev_growth, y) for y in years])
    table.add_row(label_cell("순이익 성장률"), *[growth_cell(ni_growth, y) for y in years])

    table.add_row(*section_header_row(years, "▸ 재무상태"))
    for label, vals in (
        ("총자산", data.assets),
        ("부채", data.liabilities),
        ("자기자본", data.stockholdersequity),
    ):
        table.add_row(label_cell(label), *[raw_cell(vals, y) for y in years])

    table.add_row(*section_header_row(years, "▸ 수익성 지표"))
    for label, vals in (
        ("ROE  자기자본이익률", roe_val),
        ("ROA  총자산이익률", roa_val),
        ("OPM  영업이익률", opm_val),
        ("NPM  순이익률", npm_val),
    ):
        table.add_row(label_cell(label), *[pct_cell(vals, y) for y in years])

    table.add_row(*section_header_row(years, "▸ 안정성 지표"))
    table.add_row(label_cell("DER  부채자본비율"), *[pct_cell(der_val, y) for y in years])
    table.add_row(label_cell("DR   총부채비율"), *[pct_cell(dr_val, y) for y in years])
    table.add_row(label_cell("ER   자기자본비율"), *[pct_cell(er_val, y) for y in years])
    table.add_row(label_cell("AT   자산회전율"), *[x_cell(at_val, y) for y in years])
    table.add_row(label_cell("EM   재무레버리지"), *[x_cell(em_val, y) for y in years])

    table.add_row(*section_header_row(years, "▸ DuPont 분석 "))
    table.add_row(label_cell("NPM  순이익률"), *[pct_cell(npm_val, y) for y in years])
    table.add_row(label_cell("AT   자산회전율"), *[x_cell(at_val, y) for y in years])
    table.add_row(label_cell("EM   재무레버리지"), *[x_cell(em_val, y) for y in years])
    table.add_row(label_cell("ROE  검증값"), *[pct_cell(dupont_val, y) for y in years])

    console = Console()
    console.print()
    console.print(table)



def _avg(vals):
    if not vals:
        return None
    return sum(v for _, v in vals) / len(vals)


def _scale(v: float, points: list, default: int) -> int:
    for limit, sc in points:
        if v < limit:
            return sc
    return default


PHRASE = {1: "매우 저조", 2: "저조", 3: "평균 수준", 4: "양호", 5: "우수"}
LEVEL_LABEL = {1: "위험", 2: "미흡", 3: "보통", 4: "양호", 5: "우수"}


def metric_score(key: str, v: float) -> int:
    m = METRICS[key]
    return _scale(v, m["points"], m["default"])


def metric_color(key: str, v: float) -> str:
    sc = metric_score(key, v)
    if sc <= 2:
        return "red"
    if sc == 3:
        return "yellow"
    return "green"


def metric_phrase(key: str, v: float) -> str:
    return PHRASE[metric_score(key, v)]


def _cell(v: float, metric_key: str = None, fmt: str = "pct") -> Text:
    if fmt == "x":
        return Text(f"{v:.2f}x")
    text = f"{v:+.2f}%" if fmt == "growth" else f"{v:.2f}%"
    t = Text(text)
    if metric_key:
        t.stylize(metric_color(metric_key, v))
    return t


def _series_text(vals, metric_key: str = None, fmt: str = "pct") -> Text:
    s = sorted(vals, key=lambda x: x[0])
    result = Text()
    for i, (_, v) in enumerate(s):
        result.append_text(_cell(v, metric_key, fmt))
        if i < len(s) - 1:
            result.append("  →  ")
    return result


def _print_row(console: Console, label: str, vals, metric_key: str = None, fmt: str = "pct", label_width: int = 24):
    row = Text()
    row.append(f"  {_ljust(label, label_width)}")
    row.append_text(_series_text(vals, metric_key, fmt))
    console.print(row)


def evaluate(roe_val, roa_val, opm_val, npm_val, er_val, der_val, dr_val, rev_growth, ni_growth):
    reasons = []

    def add(key, vals, label=None):
        avg_v = _avg(vals)
        if avg_v is None:
            return
        sc = metric_score(key, avg_v)
        reasons.append((label or METRICS[key]["label"], avg_v, sc))

    add("roe", roe_val)
    add("roa", roa_val)
    add("opm", opm_val)
    add("npm", npm_val)
    add("er", er_val)
    add("der", der_val)
    add("dr", dr_val)
    add("growth", rev_growth + ni_growth, label="성장률")

    if not reasons:
        return None, None, []

    avg_score = sum(sc for _, _, sc in reasons) / len(reasons)
    level = max(1, min(5, round(avg_score)))
    return level, LEVEL_LABEL[level], reasons


def print_summary(ticker: str, data, sector: str = ""):
    roe_val = roe(data.netincomeloss, data.stockholdersequity)
    roa_val = roa(data.netincomeloss, data.assets)
    opm_val = opm(data.operatingincomeloss, data.revenues)
    npm_val = npm(data.netincomeloss, data.revenues)
    der_val = der(data.liabilities, data.stockholdersequity)
    er_val = er(data.stockholdersequity, data.assets)
    at_val = at(data.revenues, data.assets)
    dr_val = debt_ratio(data.liabilities, data.assets)
    em_val = equity_multiplier(data.assets, data.stockholdersequity)
    rev_growth = yoy_growth(data.revenues)
    ni_growth = yoy_growth(data.netincomeloss)

    years = sorted(set(
        d[:4]
        for ds in (data.revenues, data.netincomeloss, data.operatingincomeloss,
                   data.assets, data.liabilities, data.stockholdersequity)
        for d, _ in ds if len(d) >= 4
    ))
    year_range = f"{years[0]} – {years[-1]}" if len(years) >= 2 else (years[0] if years else "")

    console = Console()
    console.print()
    header = Text()
    header.append(f" {ticker} ", style="bold")
    if sector:
        header.append(f" {sector} ", style="cyan")
    header.append(f"  {year_range}", style="dim")
    console.print(header)
    console.print()

    _print_row(console, "매출 성장률", rev_growth, metric_key="growth", fmt="growth")
    _print_row(console, "순이익 성장률", ni_growth, metric_key="growth", fmt="growth")
    console.print()

    _print_row(console, "ROE (자기자본이익률)", roe_val, metric_key="roe", fmt="pct")
    _print_row(console, "ROA (총자산이익률)", roa_val, metric_key="roa", fmt="pct")
    _print_row(console, "OPM (영업이익률)", opm_val, metric_key="opm", fmt="pct")
    _print_row(console, "NPM (순이익률)", npm_val, metric_key="npm", fmt="pct")
    console.print()

    _print_row(console, "DER (부채자본비율)", der_val, metric_key="der", fmt="pct")
    _print_row(console, "DR (총부채비율)", dr_val, metric_key="dr", fmt="pct")
    _print_row(console, "ER (자기자본비율)", er_val, metric_key="er", fmt="pct")
    _print_row(console, "AT (자산회전율)", at_val, fmt="x")
    _print_row(console, "EM (재무레버리지)", em_val, fmt="x")
    console.print()

    level, label, reasons = evaluate(roe_val, roa_val, opm_val, npm_val, er_val, der_val, dr_val, rev_growth, ni_growth)
    if level is not None:
        color = {1: "red", 2: "red", 3: "yellow", 4: "green", 5: "green"}[level]
        verdict = Text()
        verdict.append("  종합 평가  ")
        verdict.append(f"{label}", style=f"bold {color}")
        verdict.append(f"  ({level}/5단계)", style="dim")
        console.print(verdict)

        strongest = max(reasons, key=lambda r: r[2])
        weakest = min(reasons, key=lambda r: r[2])
        console.print(f"  강점: {strongest[0]}  (평균 {strongest[1]:.2f}%, {PHRASE[strongest[2]]})", style="dim")
        console.print(f"  약점: {weakest[0]}  (평균 {weakest[1]:.2f}%, {PHRASE[weakest[2]]})", style="dim")
        console.print()
