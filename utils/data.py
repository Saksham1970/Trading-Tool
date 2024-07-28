from utils import database
from utils.config import HOLIDAY_COMPENSATION_FACTOR, SETTINGS
from utils.api import fetch_exchange_info


def get_current_tickers():
    # Query to get unique symbols from AlertsWatchlist and Watchlists
    return [
        ticker[0]
        for ticker in database.get_data_query(
            """
        SELECT DISTINCT Symbol
        FROM (
            SELECT Symbol FROM AlertsWatchlist
            UNION
            SELECT unnest(Symbols) AS Symbol FROM Watchlists
        ) AS combined_symbols;
        """
        )
    ]


def days_to_fetch():
    days = 0
    if "RVols" in SETTINGS:
        days = max(SETTINGS["RVols"])
    return int(days * HOLIDAY_COMPENSATION_FACTOR)


def get_minimum_weekdays(tickers):
    tickers_tuple = tuple(tickers)  # Convert list to tuple
    query = "SELECT DISTINCT Exchange, Symbol FROM YFSymbol WHERE Symbol IN %s"

    database.cursor.execute(query, (tickers_tuple,))

    exchanges = database.cursor.fetchall()
    for exchange, symbol in exchanges:
        if not database.is_present("ExchangeInfo", Exchange=exchange):
            fetch_exchange_info(exchange, symbol)

    exchanges = [exchange[0] for exchange in exchanges]
    exchanges_tuple = tuple(exchanges)  # Convert list to tuple
    query = "SELECT WeekMask FROM ExchangeInfo WHERE Exchange IN %s"
    database.cursor.execute(query, (exchanges_tuple,))

    weekmasks = database.cursor.fetchall()
    weekmasks = [len(weekmask[0].split()) for weekmask in weekmasks]
    return min(weekmasks)
