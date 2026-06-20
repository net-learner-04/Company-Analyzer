from dotenv import load_dotenv
load_dotenv()

import sys
import calculate
import extract_edinet
import extract_sec
import parse


def main():
    args = sys.argv
    if len(args) < 2:
        print(f"사용법: {args[0]} <ticker>", file=sys.stderr)
        print(f"  미국 주식: {args[0]} AAPL", file=sys.stderr)
        print(f"  일본 주식: {args[0]} JP:7203  (증권코드 4자리)", file=sys.stderr)
        sys.exit(1)

    input_ticker = args[1].upper()

    if input_ticker.startswith("JP:"):
        sec_code = input_ticker[len("JP:"):]
        data = extract_edinet.get_data(sec_code)
        calculate.print_table(input_ticker, data)
    else:
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
