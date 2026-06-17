from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text


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
