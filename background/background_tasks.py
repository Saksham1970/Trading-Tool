import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from datetime import datetime
import yfinance as yf
from utils import database
from utils.startup import process_multiple_ticker_df
import pytz

import pandas as pd
from utils.config import MARKET_CLOSE_UPDATE_TD, SETTINGS
from utils import database

from yflive import QuoteStreamer
import asyncio
import websockets
import json
from utils.data import get_current_tickers

from collections import defaultdict

symbol_averages = defaultdict(lambda: defaultdict(float))
streamer = QuoteStreamer()


def update_averages(exchange):
    if "RVols" not in SETTINGS or not SETTINGS["RVols"]:
        return

    days = SETTINGS["RVols"]
    for day in days:
        results = database.cursor.execute(
            """SELECT Symbol, AVG(Volume) FROM Stocks 
            WHERE Exchange = %s AND
            Date > CURRENT_DATE - INTERVAL %s DAY""",
            (exchange, day),
        ).fetchall()

        for symbol, avg_volume in results:
            symbol_averages[symbol][day] = avg_volume


def download_daily_data():
    # Get current UTC time
    current_time = datetime.now(pytz.UTC)

    # Fetch all exchanges and their closing times
    exchanges = database.get_data_query(
        "SELECT Exchange, MarketClose, WeekMask FROM ExchangeInfo"
    )

    dfs = {}
    for exchange, market_close, weekmask in exchanges:
        # Convert market close time to UTC
        market_close_utc = market_close.replace(tzinfo=pytz.UTC)

        # Check if current time is past market close plus 1 hour
        if current_time.strftime("%a") in weekmask and current_time > (
            market_close_utc + MARKET_CLOSE_UPDATE_TD
        ):
            # Fetch all symbols for this exchange

            symbols = [
                row[0]
                for row in database.get_data_query(
                    "SELECT Symbol FROM YFSymbol WHERE Exchange = %s", (exchange,)
                )
            ]
            data = yf.download(
                symbols, period="1d", interval="1d", threads=True, group_by="ticker"
            )

            df = process_multiple_ticker_df(data, "1d", symbols)
            dfs[exchange] = df
    if dfs:
        df = pd.concat(dfs.values())
        database.bulk_insert_data("Stocks", df)
        for exchange in dfs:
            update_averages(exchange)

    print("Daily data download completed.")


quote_queue = asyncio.Queue()


async def send_quotes(websocket):

    while True:
        quote = await quote_queue.get()

        await websocket.send(json.dumps(quote))


def on_quote(qs, quote):
    
    print("Quote Recieved")
    processed_quote = {
        "symbol": quote.identifier,
        "price": quote.price,
    }

    database.cursor.execute(
        """SELECT AlertId, AlertValue, AlertOperator FROM AlertsWatchlist
                                     WHERE Symbol = %s and AlertActive = True""",
        (quote.identifier,),
    )

    alerts = database.cursor.fetchall()
    alerts_hit = []
    for alert_id, alert_value, alert_operator in alerts:
        if (alert_operator and quote.price > alert_value) or (
            not alert_operator and quote.price < alert_value
        ):
            database.update_data(
                "AlertsWatchlist", "AlertActive=False", AlertId=alert_id
            )
            alerts_hit.append(alert_id)

    processed_quote["alerts"] = alerts_hit

    for days in SETTINGS["RVols"]:
        if symbol_averages[quote.identifier][days] > 0:
            processed_quote[f"rvol_{days}"] = (
                quote.dayVolume / symbol_averages[quote.identifier][days]
            )

    quote_queue.put_nowait(processed_quote)


async def ws():
    server = await websockets.serve(send_quotes, "localhost", 8765)
    print("Quote server started on localhost:8765")
    await server.wait_closed()


def start_quote_streaming():
    streamer.on_quote = on_quote
    symbols = get_current_tickers()
    streamer.subscribe(symbols)
    streamer.start(should_thread=True)

    # Start the WebSocket server in the main thread
    asyncio.run(ws())

    try:
        # Keep the main thread alive
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down...")
        # Implement proper shutdown mechanism here
