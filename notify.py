import os, time, requests, calculate, parse


def build_payload(ticker: str, data: "parse.Data", sector: str = "") -> dict:
    text = calculate.build_report_ansi(ticker, data, sector)

    if "표시할 데이터가 없습니다" in text:
        return {
            "username": "재무 분석",
            "embeds": [{"title": ticker, "description": "표시할 데이터가 없습니다.", "color": 0x2b2d42}],
        }

    return {
        "username": "재무 분석",
        "embeds": [
            {
                "description": f"```{text[:3900]}```",
                "color": 0x2b2d42,
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
