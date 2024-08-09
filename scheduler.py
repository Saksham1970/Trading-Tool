from app_config import socketio
from dotenv import load_dotenv

load_dotenv()
import asyncio
import json
from datetime import datetime
import yfinance as yf
import pytz
import pandas as pd
from collections import defaultdict
from yflive import QuoteStreamer
from apscheduler.schedulers.background import BackgroundScheduler

from utils import database
from utils.startup import process_multiple_ticker_df
from utils.config import MARKET_CLOSE_UPDATE_TD, SETTINGS
from utils.data import get_current_tickers

symbol_averages = defaultdict(lambda: defaultdict(float))
streamer = QuoteStreamer()
daily_updated = defaultdict(datetime.date)

scheduler = BackgroundScheduler()


def setup_scheduler():
    scheduler.add_job(download_daily_data, "interval", hours=1)
    scheduler.start()
    update_all_averages()


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


async def update_streamer_symbols(cursor):
    while True:
        cursor.execute("SELECT Symbol FROM StreamedSymbols")
        symbols = cursor.fetchall()
        if symbols:
            symbols = [symbol[0] for symbol in symbols]

            if not database.is_present("Stocks", Symbol=symbols[0]):
                await asyncio.sleep(10)
                continue

            update_averages(symbols)
            streamer.subscribe(symbols)

            cursor.execute("TRUNCATE StreamedSymbols")
            cursor.connection.commit()

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
    print("Raw quote:", processed_quote)
    serialized_quote = json.dumps(processed_quote)
    print("Serialized quote:", serialized_quote)
    print("Active SocketIO clients:", len(socketio.server.eio.sockets))
    socketio.emit("quote", serialized_quote, namespace="/quotes")
    print("Quote emitted")


def start_quote_streaming():
    print("Starting quote streaming")
    streamer.on_quote = on_quote
    symbols = get_current_tickers()
    streamer.subscribe(symbols)
    streamer.start(should_thread=True)

    print("Quote streaming started")

    new_cursor = database.get_new_cursor()

    while True:
        socketio.sleep(10)
        asyncio.run(update_streamer_symbols(new_cursor))


@socketio.on("connect", namespace="/quotes")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect", namespace="/quotes")
def handle_disconnect():
    print("Client disconnected")
