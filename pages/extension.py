from app_config import app
from flask import request, jsonify

import utils.database as database
from utils.llm_comparison import yfinance_from_tradingview
from pages.alert import add_alert
from utils.data import get_current_tickers
from utils.startup import update_tickers
from utils.api import search_yfinance_tickers


def add_yf_data(yf_data):
    symbol = yf_data["symbol"]
    if not database.is_present("YFSymbol", symbol=symbol):
        keys = [
            "exchange",
            "shortname",
            "quoteType",
            "symbol",
            "index",
            "score",
            "typeDisp",
            "longname",
            "exchDisp",
            "sector",
            "sectorDisp",
            "industry",
            "industryDisp",
            "isYahooFinance",
        ]
        for key in keys:
            if key not in yf_data:
                yf_data[key] = None

        yf_data["indexName"] = yf_data["index"]
        del yf_data["index"]
        database.insert_data("YFSymbol", **yf_data)


@app.route("/yfinance_direct_alert", methods=["POST"])
def yfinance_direct_alert():
    req = request.json
    symbol = req["symbol"]
    if not database.is_present("YFSymbol", symbol=symbol):
        results = search_yfinance_tickers(symbol)
        for result in results:
            if result["symbol"] == symbol:
                break
        else:
            return jsonify({"status": "error", "message": "Symbol not found"})
        try:
            add_yf_data(result)

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    price = req["price"]
    tickers = get_current_tickers()
    if symbol not in tickers:
        update_tickers([symbol])

    if add_alert(symbol, price):
        print(f"Alert added for {symbol} at {price}")

    return jsonify({"status": "success", "message": "Data received"})


@app.route("/extension_receive", methods=["POST"])
def extension_receive():
    req = request.json

    if req["action"] == "addToWatchlist":
        print(f"Adding {req['symbol']} to Alert Watchlist")
        data = req["additionalData"]
        data["symbol"] = req["symbol"]

        if not database.is_present(
            "SymbolMapping",
            TVSymbol=req["symbol"],
            Description=data["details-description"],
            Exchange=data["details-exchange"],
            AdditionalMain=data["details-additional-main"],
            AdditionalSecondary=data["details-additional-secondary"],
        ):
            try:
                yfdata = yfinance_from_tradingview(data)
                if not yfdata:
                    raise Exception("Symbol not found on Yahoo Finance")

                database.insert_data(
                    "SymbolMapping",
                    TVSymbol=req["symbol"],
                    YFSymbol=yfdata["symbol"],
                    Description=data["details-description"],
                    Exchange=data["details-exchange"],
                    AdditionalMain=data["details-additional-main"],
                    AdditionalSecondary=data["details-additional-secondary"],
                )

                add_yf_data(yfdata)
            except Exception as e:
                print(f"Error adding to watchlist: {e}")
                return jsonify(
                    {"status": "error", "message": "Error adding to watchlist"}
                )
            symbol = yfdata["symbol"]

        else:
            symbol = database.get_data(
                "SymbolMapping",
                __dictionary=True,
                TVSymbol=req["symbol"],
                Description=data["details-description"],
                Exchange=data["details-exchange"],
                AdditionalMain=data["details-additional-main"],
                AdditionalSecondary=data["details-additional-secondary"],
            )[0]["yfsymbol"]

        price = req["price"]
        tickers = get_current_tickers()
        if symbol not in tickers:
            update_tickers([symbol])

        if add_alert(symbol, price):
            print(f"Alert added for {symbol} at {price}")

    return jsonify({"status": "success", "message": "Data received"})
