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


import asyncio
import websockets
import json
from utils.data import get_current_tickers
import time

from yflive import QuoteStreamer
from collections import defaultdict
from asyncio import Queue

ws_queue = Queue()
symbol_averages = defaultdict(lambda: defaultdict(float))
streamer = QuoteStreamer()
daily_updated = defaultdict(datetime.date)


def update_all_averages():
    if "RVols" not in SETTINGS or not SETTINGS["RVols"]:
        return

    days = SETTINGS["RVols"]
    for day in days:
        database.cursor.execute(
            """SELECT Symbol, AVG(Volume) FROM Stocks 
            WHERE Time > CURRENT_DATE - INTERVAL %s DAY
            GROUP BY Symbol""",
            (str(day),),
        )
        results = database.cursor.fetchall()
        if results:
            for symbol, avg_volume in results:
                symbol_averages[symbol][day] = avg_volume


def update_averages(symbols):
    if "RVols" not in SETTINGS or not SETTINGS["RVols"]:
        return

    days = SETTINGS["RVols"]
    for day in days:
        database.cursor.execute(
            """SELECT Symbol, AVG(Volume) FROM Stocks 
            WHERE Symbol = ANY(%s) AND
            Time > CURRENT_DATE - INTERVAL %s DAY
            GROUP BY Symbol""",
            (symbols, str(day)),
        )

        results = database.cursor.fetchall()

        for symbol, avg_volume in results:
            symbol_averages[symbol][day] = avg_volume


def update_streamer_symbols():
    while True:
        # Fetch all symbols from StreamedSymbols table
        symbols = database.get_data_query("SELECT Symbol FROM StreamedSymbols")
        if symbols:
            symbols = [symbol[0] for symbol in symbols]

            # Update streamer subscriptions

            if not database.is_present("Stocks", Symbol=symbols[0]):
                time.sleep(10)
                continue

            update_averages(symbols)
            streamer.subscribe(symbols)

            database.cursor.execute("TRUNCATE StreamedSymbols")
            database.conn.commit()

        time.sleep(10)


def download_daily_data():
    # Get current UTC time
    current_time = datetime.now(pytz.UTC)

    # Fetch all exchanges and their closing times
    exchanges = database.get_data_query(
        "SELECT Exchange, MarketClose, WeekMask FROM ExchangeInfo"
    )

    dfs = {}
    symbol_set = set()
    for exchange, market_close, weekmask in exchanges:
        # Convert market close time to UTC
        market_close_utc = market_close.replace(tzinfo=pytz.UTC)

        # Check if current time is past market close plus 1 hour
        if (
            current_time.date != daily_updated[exchange]
            and current_time.strftime("%a") in weekmask
            and current_time > (market_close_utc + MARKET_CLOSE_UPDATE_TD)
        ):
            # Fetch all symbols for this exchange

            symbols = [
                row[0]
                for row in database.get_data_query(
                    "SELECT Symbol FROM YFSymbol WHERE Exchange = %s", (exchange,)
                )
            ]
            for symbol in symbols:
                symbol_set.add(symbol)

            data = yf.download(
                symbols, period="1d", interval="1d", threads=True, group_by="ticker"
            )

            df = process_multiple_ticker_df(data, "1d", symbols)
            dfs[exchange] = df
            daily_updated[exchange] = current_time.date
    if dfs:
        df = pd.concat(dfs.values())
        database.bulk_insert_data("Stocks", df)
        update_averages(list(symbol_set))

    print("Daily data download completed.")


async def send_quotes(websocket):

    while True:
        quote = await ws_queue.get()

        await websocket.send(json.dumps(quote))


def on_quote(qs, quote):

    # print("Quote Recieved")
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
        if quote.dayVolume and symbol_averages[quote.identifier][days] > 0:
            processed_quote[f"rvol_{days}"] = float(
                quote.dayVolume / symbol_averages[quote.identifier][days]
            )

    ws_queue.put_nowait(processed_quote)


async def ws():
    server = await websockets.serve(send_quotes, "localhost", 8765)
    print("Quote server started on localhost:8765")
    await server.wait_closed()


def start_quote_streaming():
    update_all_averages()
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
