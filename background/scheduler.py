import sys
import os
import asyncio
import websockets
import json
import signal
from datetime import datetime
import yfinance as yf
import pytz
import pandas as pd
from collections import defaultdict
from yflive import QuoteStreamer
from apscheduler.schedulers.asyncio import AsyncIOScheduler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import database
from utils.startup import process_multiple_ticker_df
from utils.config import MARKET_CLOSE_UPDATE_TD, SETTINGS
from utils.data import get_current_tickers
import queue

ws_queue = queue.Queue()
symbol_averages = defaultdict(lambda: defaultdict(float))
streamer = QuoteStreamer()
daily_updated = defaultdict(datetime.date)


shutdown_flag = False


async def shutdown(loop):
    """Cleanup tasks tied to the service's shutdown."""
    global shutdown_flag
    shutdown_flag = True

    print("Shutting down...")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        task.cancel()

    print(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)

    loop.stop()


def signal_handler(sig, frame):
    print(f"Received signal {sig}")
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown(loop))


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


async def update_streamer_symbols():
    while True:
        symbols = database.get_data_query("SELECT Symbol FROM StreamedSymbols")
        if symbols:
            symbols = [symbol[0] for symbol in symbols]

            if not database.is_present("Stocks", Symbol=symbols[0]):
                await asyncio.sleep(10)
                continue

            update_averages(symbols)
            streamer.subscribe(symbols)

            database.cursor.execute("TRUNCATE StreamedSymbols")
            database.conn.commit()

        await asyncio.sleep(10)


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


async def handle_connection(websocket):
    try:
        while True:
            await asyncio.sleep(1)
            try:
                quote = ws_queue.get(timeout=0.1)
                await websocket.send(json.dumps(quote))
            except queue.Empty:
                # Check if we should shut down
                if shutdown_flag:
                    break
                continue
            except websockets.exceptions.ConnectionClosed:
                print("Client connection closed")
                break
    finally:
        print("Connection handler completed")


def on_quote(qs, quote):
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
    if "RVols" in SETTINGS and SETTINGS["RVols"]:
        for days in SETTINGS["RVols"]:
            if quote.dayVolume and symbol_averages[quote.identifier][days] > 0:
                processed_quote[f"rvol_{days}"] = float(
                    quote.dayVolume / symbol_averages[quote.identifier][days]
                )
    ws_queue.put(processed_quote)


async def process_queue():
    while not shutdown_flag:
        try:
            quote = ws_queue.get(timeout=0.1)
            for client in connected_clients:
                try:
                    await client.send(json.dumps(quote))
                except websockets.exceptions.ConnectionClosed:
                    connected_clients.remove(client)
        except queue.Empty:
            await asyncio.sleep(0.01)


async def start_quote_streaming():
    global shutdown_flag, connected_clients
    connected_clients = set()

    streamer.on_quote = on_quote
    symbols = get_current_tickers()
    streamer.subscribe(symbols)
    streamer.start(should_thread=True)

    async def handler(websocket):
        connected_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            connected_clients.remove(websocket)

    server = await websockets.serve(handler, "localhost", 8765)
    print("Quote server started on localhost:8765")

    queue_task = asyncio.create_task(process_queue())

    try:
        while not shutdown_flag:
            await asyncio.sleep(1)
    finally:
        server.close()
        await server.wait_closed()
        streamer.stop()
        queue_task.cancel()
        await queue_task


async def main():
    global main_loop
    main_loop = asyncio.get_event_loop()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(download_daily_data, "interval", hours=1)
    scheduler.start()
    update_all_averages()

    try:
        await asyncio.gather(start_quote_streaming(), update_streamer_symbols())
    finally:
        scheduler.shutdown()
        print("Shutdown complete.")


if __name__ == "__main__":
    if sys.platform == "win32":
        # Windows-specific signal handling
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    else:
        # Unix-like systems can use asyncio's add_signal_handler
        loop = asyncio.get_event_loop()
        for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(loop)))

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught in main.")
    finally:
        print("Main shutdown complete.")
