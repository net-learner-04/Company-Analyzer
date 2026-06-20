import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import calculate
import parse


def _raw_html(vals, year: str) -> str:
    found = next(((d, v) for d, v in vals if len(d) >= 4 and d[:4] == year), None)
    if not found:
        return "<td>N/A</td>"
    text = calculate.fmt_val(found[1])
    style = " style='color:#c0392b'" if found[1] < 0 else ""
    return f"<td{style}>{text}</td>"


def _pct_html(vals, year: str) -> str:
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    if not found:
        return "<td>N/A</td>"
    text = f"{found[1]:.2f}%"
    if found[1] < 0.0:
        style = " style='color:#c0392b'"
    elif found[1] >= 15.0:
        style = " style='color:#27ae60'"
    else:
        style = ""
    return f"<td{style}>{text}</td>"


def _growth_html(vals, year: str) -> str:
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    if not found:
        return "<td>N/A</td>"
    text = f"{found[1]:+.2f}%"
    if found[1] < 0.0:
        style = " style='color:#c0392b'"
    elif found[1] > 0.0:
        style = " style='color:#27ae60'"
    else:
        style = ""
    return f"<td{style}>{text}</td>"


def _x_html(vals, year: str) -> str:
    found = next(((yr, v) for yr, v in vals if yr == year), None)
    if not found:
        return "<td>N/A</td>"
    return f"<td>{found[1]:.2f}x</td>"


def _section_row(years: list, title: str) -> str:
    empty = "".join("<td></td>" for _ in years)
    return f"<tr class='section'><td>{title}</td>{empty}</tr>"


def _data_row(label: str, cells: list) -> str:
    return f"<tr><td class='label'>{label}</td>{''.join(cells)}</tr>"


def build_html(ticker: str, data: "parse.Data") -> str:
    roe_val = calculate.roe(data.netincomeloss, data.stockholdersequity)
    roa_val = calculate.roa(data.netincomeloss, data.assets)
    opm_val = calculate.opm(data.operatingincomeloss, data.revenues)
    npm_val = calculate.npm(data.netincomeloss, data.revenues)
    der_val = calculate.der(data.liabilities, data.stockholdersequity)
    er_val = calculate.er(data.stockholdersequity, data.assets)
    at_val = calculate.at(data.revenues, data.assets)
    dr_val = calculate.debt_ratio(data.liabilities, data.assets)
    em_val = calculate.equity_multiplier(data.assets, data.stockholdersequity)
    rev_growth = calculate.yoy_growth(data.revenues)
    ni_growth = calculate.yoy_growth(data.netincomeloss)
    dupont_val = calculate.dupont(npm_val, at_val, em_val)

    year_set = set()
    for ds in (data.revenues, data.netincomeloss, data.operatingincomeloss,
               data.assets, data.liabilities, data.stockholdersequity):
        for d, _ in ds:
            if len(d) >= 4:
                year_set.add(d[:4])
    for ds in (roe_val, roa_val, opm_val, npm_val, der_val, er_val,
               at_val, dr_val, em_val, rev_growth, ni_growth, dupont_val):
        for yr, _ in ds:
            year_set.add(yr)
    years = sorted(year_set)

    if not years:
        return f"<p>{ticker}: 표시할 데이터가 없습니다.</p>"

    year_headers = "".join(f"<th>{y}</th>" for y in years)

    rows = ""
    rows += _section_row(years, "손익")
    rows += _data_row("매출", [_raw_html(data.revenues, y) for y in years])
    rows += _data_row("영업이익", [_raw_html(data.operatingincomeloss, y) for y in years])
    rows += _data_row("순이익", [_raw_html(data.netincomeloss, y) for y in years])

    rows += _section_row(years, "성장률")
    rows += _data_row("매출 성장률", [_growth_html(rev_growth, y) for y in years])
    rows += _data_row("순이익 성장률", [_growth_html(ni_growth, y) for y in years])

    rows += _section_row(years, "재무상태")
    rows += _data_row("총자산", [_raw_html(data.assets, y) for y in years])
    rows += _data_row("부채", [_raw_html(data.liabilities, y) for y in years])
    rows += _data_row("자기자본", [_raw_html(data.stockholdersequity, y) for y in years])

    rows += _section_row(years, "수익성 지표")
    rows += _data_row("자기자본이익률 (ROE)", [_pct_html(roe_val, y) for y in years])
    rows += _data_row("총자산이익률 (ROA)", [_pct_html(roa_val, y) for y in years])
    rows += _data_row("영업이익률 (OPM)", [_pct_html(opm_val, y) for y in years])
    rows += _data_row("순이익률 (NPM)", [_pct_html(npm_val, y) for y in years])

    rows += _section_row(years, "안정성 지표")
    rows += _data_row("부채자본비율 (DER)", [_pct_html(der_val, y) for y in years])
    rows += _data_row("총부채비율 (DR)", [_pct_html(dr_val, y) for y in years])
    rows += _data_row("자기자본비율 (ER)", [_pct_html(er_val, y) for y in years])
    rows += _data_row("자산회전율 (AT)", [_x_html(at_val, y) for y in years])
    rows += _data_row("재무레버리지 (EM)", [_x_html(em_val, y) for y in years])

    rows += _section_row(years, "DuPont 분석")
    rows += _data_row("순이익률 (NPM)", [_pct_html(npm_val, y) for y in years])
    rows += _data_row("자산회전율 (AT)", [_x_html(at_val, y) for y in years])
    rows += _data_row("재무레버리지 (EM)", [_x_html(em_val, y) for y in years])
    rows += _data_row("ROE 검증값", [_pct_html(dupont_val, y) for y in years])

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
    background: #f0f2f5;
    margin: 0;
    padding: 32px 24px;
    color: #1a1a2e;
  }}
  .wrapper {{
    max-width: 1100px;
    margin: 0 auto;
  }}
  h2 {{
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    margin: 0 0 20px 0;
    color: #1a1a2e;
  }}
  .subtitle {{
    font-size: 0.82rem;
    color: #888;
    margin-bottom: 24px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    background: #ffffff;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.07);
    font-size: 0.88rem;
  }}
  thead th {{
    background: #1a1a2e;
    color: #e8e8f0;
    font-weight: 600;
    text-align: right;
    padding: 14px 22px;
    letter-spacing: 0.04em;
    font-size: 0.82rem;
    white-space: nowrap;
  }}
  thead th:first-child {{
    text-align: left;
    min-width: 200px;
  }}
  tbody td {{
    padding: 12px 22px;
    text-align: right;
    border-bottom: 1px solid #f2f3f6;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }}
  tbody td.label {{
    text-align: left;
    font-weight: 500;
    color: #2c2c4a;
    padding-left: 28px;
  }}
  tr.section td {{
    background: #f6f7fb;
    font-weight: 700;
    color: #5a5a7a;
    text-align: left;
    padding: 10px 16px;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-top: 1px solid #e8e9f0;
    border-bottom: 1px solid #e8e9f0;
  }}
  tbody tr:not(.section):hover td {{
    background: #fafbff;
  }}
  tbody tr:last-child td {{
    border-bottom: none;
  }}
</style>
</head>
<body>
<div class="wrapper">
  <h2>{ticker} 재무제표</h2>
  <table>
    <thead>
      <tr>
        <th>{ticker}</th>
        {year_headers}
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</div>
</body>
</html>"""


def send_email(ticker: str, data: "parse.Data"):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_to = os.environ.get("SMTP_TO", "")

    missing = [k for k, v in {"SMTP_USER": smtp_user, "SMTP_PASS": smtp_pass, "SMTP_TO": smtp_to}.items() if not v]
    if missing:
        print(f".env에 다음 항목을 설정해주세요: {', '.join(missing)}")
        return

    html = build_html(ticker, data)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{ticker} 재무제표"
    msg["From"] = smtp_user
    msg["To"] = smtp_to
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, smtp_to, msg.as_string())
        print(f"이메일 전송 완료: {smtp_to}")
    except Exception as e:
        print(f"이메일 전송 실패: {e}")
