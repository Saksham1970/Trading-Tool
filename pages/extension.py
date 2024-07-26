from app_config import app, cursor
from flask import request, jsonify

import utils.database as database
from utils.llm_comparison import yfinance_from_tradingview
from pages.alert import add_alert
from utils.data import get_current_tickers
from utils.startup import update_tickers


@app.route("/extension_receive", methods=["POST"])
def extension_receive():
    req = request.json
    if req["action"] == "addToWatchlist":
        print(f"Adding {req['symbol']} to Alert Watchlist")
        data = req["additionalData"]
        data["symbol"] = req["symbol"]

        if not database.is_present(
            cursor,
            "SymbolMapping",
            TVSymbol=req["symbol"],
            Description=data["details-description"],
            Exchange=data["details-exchange"],
            AdditionalMain=data["details-additional-main"],
            AdditionalSecondary=data["details-additional-secondary"],
        ):
            try:
                yfdata = yfinance_from_tradingview(data)
                yfdata["indexName"] = yfdata["index"]
                del yfdata["index"]
                database.insert_data(
                    cursor,
                    "SymbolMapping",
                    TVSymbol=req["symbol"],
                    YFSymbol=yfdata["symbol"],
                    Description=data["details-description"],
                    Exchange=data["details-exchange"],
                    AdditionalMain=data["details-additional-main"],
                    AdditionalSecondary=data["details-additional-secondary"],
                )
                database.insert_data(cursor, "YFSymbol", **yfdata)

            except Exception as e:
                print(f"Error adding to watchlist: {e}")
                return jsonify(
                    {"status": "error", "message": "Error adding to watchlist"}
                )
            symbol = yfdata["symbol"]

        else:
            symbol = database.get_data(
                cursor,
                "SymbolMapping",
                __dictionary=True,
                TVSymbol=req["symbol"],
                Description=data["details-description"],
                Exchange=data["details-exchange"],
                AdditionalMain=data["details-additional-main"],
                AdditionalSecondary=data["details-additional-secondary"],
            )[0]["yfsymbol"]

        price = req["price"]
        tickers = get_current_tickers(cursor)
        if symbol not in tickers:
            update_tickers(cursor, [symbol])

        if add_alert(symbol, price):
            print(f"Alert added for {symbol} at {price}")

    return jsonify({"status": "success", "message": "Data received"})
