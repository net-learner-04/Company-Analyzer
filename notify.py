import os, time, requests, calculate, parse


def _years(data) -> list:
    return sorted(set(
        d[:4]
        for ds in (data.revenues, data.netincomeloss, data.operatingincomeloss,
                   data.assets, data.liabilities, data.stockholdersequity)
        for d, _ in ds if len(d) >= 4
    ))


def _series_str(vals, fmt: str = "pct") -> str:
    s = sorted(vals, key=lambda x: x[0])
    parts = [f"{v:+.2f}%" if fmt == "growth" else (f"{v:.2f}x" if fmt == "x" else f"{v:.2f}%") for _, v in s]
    return "  →  ".join(parts)


def _metric_line(key: str, vals, fmt: str = "pct", label: str = None) -> str:
    meta = calculate.METRICS[key]
    display_label = label or meta["label"]
    avg = calculate._avg(vals)
    if avg is None:
        return f"**{display_label}**\n데이터 없음"
    score = calculate.metric_score(key, avg)
    phrase = calculate.PHRASE[score]
    series = _series_str(vals, fmt)
    avg_str = f"{avg:+.2f}%" if fmt == "growth" else f"{avg:.2f}%"
    return (
        f"**{display_label}** — {phrase}\n"
        f"{series}  (평균 {avg_str})\n"
        f"{meta['desc']}"
    )


def _info_line(label: str, vals, desc: str) -> str:
    avg = calculate._avg(vals)
    if avg is None:
        return f"**{label}**\n데이터 없음"
    series = _series_str(vals, "x")
    return f"**{label}**\n{series}  (평균 {avg:.2f}x)\n{desc}"


def build_payload(ticker: str, data: "parse.Data", sector: str = "") -> dict:
    years = _years(data)
    if not years:
        return {
            "username": "재무 분석",
            "embeds": [{"title": ticker, "description": "표시할 데이터가 없습니다.", "color": 0x2b2d42}],
        }

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

    year_range = f"{years[0]} – {years[-1]}" if len(years) >= 2 else years[0]

    growth_value = (
        _metric_line("growth", rev_growth, "growth", label="매출 성장률")
        + "\n\n"
        + _metric_line("growth", ni_growth, "growth", label="순이익 성장률")
    )

    profit_value = "\n\n".join([
        _metric_line("roe", roe_val),
        _metric_line("roa", roa_val),
        _metric_line("opm", opm_val),
        _metric_line("npm", npm_val),
    ])

    stability_value = "\n\n".join([
        _metric_line("er", er_val),
        _metric_line("der", der_val),
        _metric_line("dr", dr_val),
    ])

    reference_value = "\n\n".join([
        _info_line("AT (자산회전율)", at_val, "자산을 매출로 전환하는 효율 (참고 지표, 업종별 편차 큼)"),
        _info_line("EM (재무레버리지)", em_val, "자산 대비 자기자본 레버리지 배수 (참고 지표)"),
    ])

    level, label, reasons = calculate.evaluate(
        roe_val, roa_val, opm_val, npm_val, er_val, der_val, dr_val, rev_growth, ni_growth
    )

    fields = [
        {"name": "성장성", "value": growth_value[:1024], "inline": False},
        {"name": "수익성", "value": profit_value[:1024], "inline": False},
        {"name": "안정성", "value": stability_value[:1024], "inline": False},
        {"name": "참고 지표", "value": reference_value[:1024], "inline": False},
    ]

    if level is not None:
        strongest = max(reasons, key=lambda r: r[2])
        weakest = min(reasons, key=lambda r: r[2])
        verdict_value = (
            f"**{label}** ({level}/5단계)\n\n"
            f"강점: {strongest[0]} — 평균 {strongest[1]:.2f}% ({calculate.PHRASE[strongest[2]]})\n"
            f"약점: {weakest[0]} — 평균 {weakest[1]:.2f}% ({calculate.PHRASE[weakest[2]]})\n\n"
        )
        fields.append({"name": "종합 평가", "value": verdict_value[:1024], "inline": False})

    title = f"{ticker}  {sector}  |  {year_range}" if sector else f"{ticker}  |  {year_range}"

    return {
        "username": "재무 분석",
        "embeds": [
            {
                "title": title,
                "color": 0x2b2d42,
                "fields": fields,
                "footer": {"text": "SEC EDGAR 데이터 기반"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        ],
    }


def send_discord(ticker: str, data: "parse.Data", sector: str = ""):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        print(".env에 DISCORD_WEBHOOK_URL을 설정해주세요.")
        return

    payload = build_payload(ticker, data, sector)

    try:
        r = requests.post(webhook_url, json=payload, timeout=10)
        if r.status_code in (200, 204):
            print("Discord 전송 완료")
        else:
            print(f"Discord 응답 실패: {r.status_code}: {r.text}")
    except requests.RequestException as e:
        print(f"Discord 전송 실패: {e}")
