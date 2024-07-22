import requests
import json
from ratelimit import limits
from datetime import timedelta, datetime
import yfinance as yf

from utils import database
from utils.config import API_CALLS, API_RATE_LIMIT


def ceil_dt(dt, delta):
    return dt + (datetime.min.replace(tzinfo=dt.tzinfo) - dt) % delta


@limits(calls=API_CALLS, period=API_RATE_LIMIT)
def search_yfinance_tickers(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(
        f"https://query2.finance.yahoo.com/v1/finance/search?q={query}", headers=headers
    )

    if response.status_code == 200:
        data = json.loads(response.text)
        results = data.get("quotes", [])
        return results

    else:
        print(f"Error: Status code {response.status_code}")
        return []


def fetch_exchange_info(cursor, exchange, symbol):
    mo3data = yf.download(symbol, period="3mo", interval="1d")
    date = mo3data.iloc[-2].name
    d1data = yf.download(
        symbol, start=date, end=date + timedelta(days=1), interval="1m"
    )
    times = d1data.index
    delta = timedelta(minutes=30)

    market_open = ceil_dt(times[0], delta).timetz()
    market_close = ceil_dt(times[-1], delta).timetz()

    for i in range(len(times) - 1):
        if times[i] + timedelta(minutes=1) != times[i + 1]:
            break_start = ceil_dt(times[i], delta).timetz()
            break_end = ceil_dt(times[i + 1], delta).timetz()
            if break_start != break_end:
                break
    else:
        break_start = None
        break_end = None

    weekmask = set()
    for date in mo3data.index:
        weekmask.add(date.strftime("%a"))
    weekmask = " ".join(weekmask)

    granularity = {"_1m": len(d1data)}
    granularities = ["2m", "5m", "15m", "30m", "60m", "90m"]

    for gran in granularities:
        data = yf.download(
            symbol, start=date, end=date + timedelta(days=1), interval=gran
        )
        granularity["_" + gran] = len(data)

    database.insert_data(
        cursor,
        "ExchangeInfo",
        Exchange=exchange,
        MarketOpen=market_open,
        MarketClose=market_close,
        BreakStart=break_start,
        BreakEnd=break_end,
        WeekMask=weekmask,
        **granularity,
    )
