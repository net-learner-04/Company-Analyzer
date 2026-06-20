from dotenv import load_dotenv
load_dotenv()

import sys
import calculate
import extract_sec
import parse

def main():
    args = sys.argv
    if len(args) < 2:
        print(f"사용법: {args[0]} <ticker>", file=sys.stderr)
        print(f"  예시: {args[0]} AAPL", file=sys.stderr)
        sys.exit(1)

    input_ticker = args[1].upper()

    extract_sec.get_company_tickers()
    cik = extract_sec.return_ticker(input_ticker)
    if not cik:
        print(f"티커를 찾을 수 없습니다: {input_ticker}", file=sys.stderr)
        sys.exit(1)

    extract_sec.get_company_facts(input_ticker, cik)
    data = parse.Data.new(input_ticker)
    calculate.print_table(input_ticker, data)

if __name__ == "__main__":
    main()
