from app_config import app
from flask import request, jsonify

import utils.database as database
from utils.llm_comparison import yfinance_from_tradingview
from pages.alert import add_alert
from utils.data import get_current_tickers
from utils.startup import update_tickers
from utils.api import search_yfinance_tickers


@app.rount("/yfinance_direct_alert", methods=["POST"])
def yfinance_direct_alert():
    req = request.json
    symbol = req["symbol"]
    results = search_yfinance_tickers(symbol)
    for result in results:
        if result["symbol"] == symbol:
            break
    else:
        return jsonify({"status": "error", "message": "Symbol not found"})

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
        if key not in result:
            result[key] = None

    result["indexName"] = result["index"]
    del result["index"]

    try:
        database.insert_data("YFSymbol", **result)
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
                    if key not in yfdata:
                        yfdata[key] = None

                yfdata["indexName"] = yfdata["index"]
                del yfdata["index"]

                database.insert_data(
                    "SymbolMapping",
                    TVSymbol=req["symbol"],
                    YFSymbol=yfdata["symbol"],
                    Description=data["details-description"],
                    Exchange=data["details-exchange"],
                    AdditionalMain=data["details-additional-main"],
                    AdditionalSecondary=data["details-additional-secondary"],
                )
                database.insert_data("YFSymbol", **yfdata)

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
