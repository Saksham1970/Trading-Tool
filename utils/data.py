from utils import database
from utils.config import HOLIDAY_COMPENSATION_FACTOR, SETTINGS
from utils.api import fetch_exchange_info


def get_current_tickers(cursor):
    # Query to get unique symbols from AlertsWatchlist and Watchlists
    cursor.execute(
        """
        SELECT DISTINCT Symbol
        FROM (
            SELECT Symbol FROM AlertsWatchlist
            UNION
            SELECT unnest(Symbols) AS Symbol FROM Watchlists
        ) AS combined_symbols;
        """
    )
    return [ticker[0] for ticker in cursor.fetchall()]


def days_to_fetch():
    days = 0
    if "RVols" in SETTINGS:
        days = max(SETTINGS["RVols"])
    return int(days * HOLIDAY_COMPENSATION_FACTOR)


def get_minimum_weekdays(cursor, tickers):
    tickers_tuple = tuple(tickers)  # Convert list to tuple
    query = "SELECT DISTINCT Exchange, Symbol FROM YFSymbol WHERE Symbol IN %s"

    cursor.execute(query, (tickers_tuple,))

    exchanges = cursor.fetchall()
    for exchange, symbol in exchanges:
        if not database.is_present(cursor, "ExchangeInfo", Exchange=exchange):
            fetch_exchange_info(cursor, exchange, symbol)

    exchanges = [exchange[0] for exchange in exchanges]
    exchanges_tuple = tuple(exchanges)  # Convert list to tuple
    query = "SELECT WeekMask FROM ExchangeInfo WHERE Exchange IN %s"
    cursor.execute(query, (exchanges_tuple,))

    weekmasks = cursor.fetchall()
    weekmasks = [len(weekmask[0].split()) for weekmask in weekmasks]
    return min(weekmasks)
