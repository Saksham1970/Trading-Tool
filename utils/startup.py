from utils.data import get_current_tickers, days_to_fetch, get_minimum_weekdays
from utils import database
from utils.config import SETTINGS, REFERECE_DATETIME

import yfinance as yf
from datetime import datetime, timedelta, date
import pandas as pd
from psycopg2.extras import execute_values


def process_multiple_ticker_df(df, interval, symbols):
    df.index.name = "Time"
    df_reset = df.reset_index()

    if isinstance(df.columns, pd.MultiIndex):

        df_reset.columns = [
            "Time" if col[0] == "Time" else f"{col[0]}_{col[1]}"
            for col in df_reset.columns
        ]
        df_melted = df_reset.melt(id_vars=["Time"], var_name="temp", value_name="value")
        df_melted[["Ticker", "Price"]] = df_melted["temp"].str.split("_", expand=True)
        df_final = df_melted.drop("temp", axis=1)[["Time", "Ticker", "Price", "value"]]
        df_pivoted = df_final.pivot_table(
            index=["Time", "Ticker"], columns="Price", values="value"
        ).reset_index()

        df_pivoted["Interval"] = interval
        df_pivoted.rename(
            columns={"Ticker": "Symbol", "Adj Close": "AdjClose"}, inplace=True
        )

        df = df_pivoted
    else:
        df_reset["Interval"] = interval
        df_reset.rename(columns={"Adj Close": "AdjClose"}, inplace=True)
        df_reset["Symbol"] = symbols[0]
        df = df_reset

    if df["Time"].dtype == "object" and isinstance(df["Time"].iloc[0], date):
        df["Time"] = pd.to_datetime(df["Time"])
    if df["Time"].dt.tz is None:
        df["Time"] = df["Time"].dt.tz_localize("UTC")
    return df


def update_tickers(cursor, tickers):
    days = days_to_fetch()
    dfs = []

    if days != 0:
        days = days * 7 // get_minimum_weekdays(cursor, tickers)
        df = yf.download(
            tickers,
            start=datetime.today() - timedelta(days=days),
            end=datetime.today(),
            interval="1d",
            threads=True,
            group_by="ticker",
        )
        dfs.append(process_multiple_ticker_df(df, "1d", tickers))

    if "UpdateRanges" in SETTINGS:
        for interval in SETTINGS["UpdateRanges"]:
            df = yf.download(
                tickers,
                start=datetime.now()
                - (
                    datetime.fromisoformat(SETTINGS["UpdateRanges"][interval])
                    - REFERECE_DATETIME
                ),
                end=datetime.now(),
                interval=interval,
                threads=True,
                group_by="ticker",
            )
            dfs.append(process_multiple_ticker_df(df, interval, tickers))

    df = pd.concat(dfs)

    database.bulk_insert_data(cursor, "Stocks", df)


def startup(cursor):
    tickers = get_current_tickers(cursor)
    if not tickers:
        return
    update_tickers(cursor, tickers)
