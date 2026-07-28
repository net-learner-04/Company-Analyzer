from dotenv import load_dotenv
from pathlib import Path
import sys, calculate, notify, extract, parse

dotenv.load_dotenv(Path(__file__).parent / ".env")


def start():
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
    
    sector = extract.get_company_sic(input_ticker, cik)
    data = parse.Data.new(input_ticker)
    
    calculate.print_table(input_ticker, data)
    
    try:
        ans = input("Discord에 전송하시겠습니까? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ans = "n"
        
    if ans == "y":
        notify.send_discord(input_ticker, data, sector)
        
if __name__ == "__main__":
    start()
