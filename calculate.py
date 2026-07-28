from rich.console import Console
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


def fmt_val(v) -> str:
    sign = "-" if v < 0 else ""
    v = abs(v)
    
    if v >= 1_000_000_000_000:
        return f"{sign}{v / 1_000_000_000_000:.2f}T"
    if v >= 1_000_000_000:
        return f"{sign}{v / 1_000_000_000:.2f}B"
    if v >= 1_000_000:
        return f"{sign}{v / 1_000_000:.2f}M"
    if v >= 1_000:
        return f"{sign}{v / 1_000:.2f}K"
        
    return f"{sign}{v:.0f}"


def _collect_years(data, *extra_series) -> list:
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
    for ds in extra_series:
        for yr, _ in ds:
            years.append(yr)
            
    return sorted(set(years))


def _cell_raw(vals, year):
    found = next(((d, v) for d, v in vals if len(d) >= 4 and d[:4] == year), None)
    
    if found is None:
        return "N/A", None
        
    text = fmt_val(found[1])
    color = "red" if found[1] < 0 else None
    
    return text, color


def _cell_pct(vals, year):
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    
    if found is None:
        return "N/A", None
        
    text = f"{found[1]:.2f}%"
    
    if found[1] < 0.0:
        color = "red"
    elif found[1] >= 15.0:
        color = "green"
    else:
        color = None
        
    return text, color


def _cell_growth(vals, year):
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    
    if found is None:
        return "N/A", None
        
    text = f"{found[1]:+.2f}%"
    
    if found[1] < 0.0:
        color = "red"
    elif found[1] > 0.0:
        color = "green"
    else:
        color = None
        
    return text, color


def _cell_x(vals, year):
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    
    if found is None:
        return "N/A", None
        
    return f"{found[1]:.2f}x", None


def build_structure(ticker: str, data, sector: str = ""):
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

    years = _collect_years(
        data, roe_val, roa_val, opm_val, npm_val,
        der_val, er_val, at_val,
        dr_val, em_val,
        rev_growth, ni_growth,
    )

    if not years:
        return None

    sections = [
        ("[Income]", [
            ("Revenue", data.revenues, _cell_raw),
            ("OpIncome", data.operatingincomeloss, _cell_raw),
            ("NetIncome", data.netincomeloss, _cell_raw),
        ]),
        ("[Growth]", [
            ("RevGrowth", rev_growth, _cell_growth),
            ("NIGrowth", ni_growth, _cell_growth),
        ]),
        ("[Balance]", [
            ("Assets", data.assets, _cell_raw),
            ("Liabilities", data.liabilities, _cell_raw),
            ("Equity", data.stockholdersequity, _cell_raw),
        ]),
        ("[Profitability]", [
            ("ROE", roe_val, _cell_pct),
            ("ROA", roa_val, _cell_pct),
            ("OPM", opm_val, _cell_pct),
            ("NPM", npm_val, _cell_pct),
        ]),
        ("[Stability]", [
            ("DER", der_val, _cell_pct),
            ("DR", dr_val, _cell_pct),
            ("ER", er_val, _cell_pct),
            ("AT", at_val, _cell_x),
            ("EM", em_val, _cell_x),
        ]),
    ]

    rendered_sections = []
    
    all_labels = []
    
    max_cell_len = 0
    
    for title, rows in sections:
        rendered_rows = []
        
        for label, vals, cell_fn in rows:
            all_labels.append(label)
            cells = [cell_fn(vals, y) for y in years]
            max_cell_len = max(max_cell_len, max(len(c[0]) for c in cells))
            rendered_rows.append((label, cells))
            
        rendered_sections.append((title, rendered_rows))

    label_width = max(len(l) for l in all_labels) + 2
    col_width = max(max_cell_len, max(len(y) for y in years)) + 2

    title_line = f"{ticker}  {sector}".strip()
    unit_note = "단위: K=천 M=백만 B=십억 T=조"

    return {
        "title_line": title_line,
        "unit_note": unit_note,
        "sector": sector,
        "years": years,
        "sections": rendered_sections,
        "label_width": label_width,
        "col_width": col_width,
    }


def render_console(structure) -> None:
    console = Console()
    
    label_width = structure["label_width"]
    col_width = structure["col_width"]
    years = structure["years"]
    total_width = label_width + col_width * len(years)

    console.print()
    
    console.print(f"[bold]{structure['title_line']}\t \
        {structure['unit_note']}[/bold]")
    
    console.print()

    header = Text("".ljust(label_width))
    
    for y in years:
        header.append(y.rjust(col_width))
    console.print(header)
    console.print("-" * total_width, style="dim")

    for title, rows in structure["sections"]:
        console.print(f"[bold]{title}[/bold]")
        for label, cells in rows:
            line = Text(label.ljust(label_width))
            for text, color in cells:
                cell_text = Text(text.rjust(col_width))
                if color:
                    cell_text.stylize(color)
                line.append_text(cell_text)
            console.print(line)
        console.print("-" * total_width, style="dim")


_ANSI_RESET = "\u001b[0m"
_ANSI_COLOR = {"red": "\u001b[31m", "green": "\u001b[32m"}


def render_discord_ansi(structure) -> str:
    label_width = structure["label_width"]
    col_width = structure["col_width"]
    years = structure["years"]
    total_width = label_width + col_width * len(years)

    lines = [structure["title_line"], structure["unit_note"], structure["sector"]]

    header = "".ljust(label_width) + "".join(y.rjust(col_width) for y in years)
    lines.append(header)
    lines.append("-" * total_width)

    for title, rows in structure["sections"]:
        lines.append(title)
        for label, cells in rows:
            row = label.ljust(label_width)
            for text, color in cells:
                cell = text.rjust(col_width)
                if color:
                    cell = f"{_ANSI_COLOR[color]}{cell}{_ANSI_RESET}"
                row += cell
            lines.append(row)
        lines.append("-" * total_width)

    return "\n".join(lines).rstrip()


def print_table(ticker: str, data, sector: str = ""):
    structure = build_structure(ticker, data, sector)
    
    if structure is None:
        print(f"=== {ticker} ===")
        print("  표시할 재무 데이터가 없습니다.")
        return
        
    render_console(structure)


def build_report_ansi(ticker: str, data, sector: str = "") -> str:
    structure = build_structure(ticker, data, sector)
    
    if structure is None:
        return f"{ticker}: 표시할 데이터가 없습니다."
        
    return render_discord_ansi(structure)
