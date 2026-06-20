from dotenv import load_dotenv
load_dotenv()

import sys
import calculate
import report
import extract
import parse


def main():
    args = sys.argv
    if len(args) < 2:
        print(f"사용법: {args[0]} <ticker>", file=sys.stderr)
        print(f"  예시: {args[0]} AAPL", file=sys.stderr)
        sys.exit(1)

    input_ticker = args[1].upper()

    extract.get_company_tickers()
    cik = extract.return_ticker(input_ticker)
    if not cik:
        print(f"티커를 찾을 수 없습니다: {input_ticker}", file=sys.stderr)
        sys.exit(1)

    extract.get_company_facts(input_ticker, cik)
    data = parse.Data.new(input_ticker)

    calculate.print_summary(input_ticker, data)

    try:
        ans = input("상세 지표를 이메일로 받으시겠습니까? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ans = "n"

    if ans == "y":
        report.send_email(input_ticker, data)


if __name__ == "__main__":
    main()
