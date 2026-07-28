import os, asyncio, discord
from discord import app_commands
from dotenv import load_dotenv
from pathlib import Path
import calculate, extract, parse

load_dotenv(Path(__file__).parent / ".env")

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"{client.user} 로그인 완료")


def _fetch_data(ticker: str):
    extract.get_company_tickers()
    cik = extract.return_ticker(ticker)
    if not cik:
        return None, None
    extract.get_company_facts(ticker, cik)
    sector = extract.get_company_sic(ticker, cik)
    data = parse.Data.new(ticker)
    return data, sector


@tree.command(name="재무분석", description="티커의 연도별 재무 지표를 조회합니다")
@app_commands.describe(ticker="조회할 종목 티커 (예: AAPL)")
async def financials(interaction: discord.Interaction, ticker: str):
    await interaction.response.defer()
    ticker = ticker.upper()
    loop = asyncio.get_running_loop()
    data, sector = await loop.run_in_executor(None, _fetch_data, ticker)

    if data is None:
        await interaction.followup.send(f"티커를 찾을 수 없습니다: {ticker}")
        
        return

    text = calculate.build_report_ansi(ticker, data, sector)

    if len(text) <= 1990:
        await interaction.followup.send(f"```ansi\n{text}\n```")   
    else:
        chunk_size = 1980
        
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            await interaction.followup.send(f"```ansi\n{chunk}\n```")

client.run(TOKEN)
