import yfinance as yf
from utils import database
from app_config import app
from flask import request, jsonify
from background.background_tasks import streamer


def add_alert(symbol, price):
    current_price = yf.Ticker(symbol).history(period="1d").iloc[-1]["Close"]

    current_price, price = float(current_price), float(price.replace(",", ""))

    if current_price > price:
        dir = False
    else:
        dir = True

    database.insert_data(
        "AlertsWatchlist",
        Symbol=symbol,
        AlertValue=price,
        AlertOperator=dir,
        AlertActive=True,
    )

    streamer.subscribe([symbol])

    return True


@app.route("/add_alert", methods=["POST"])
def add_alert_route():
    req = request.json
    if add_alert(req["symbol"], req["price"]):
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})


@app.route("/delete_alert", methods=["POST"])
def delete_alert():
    req = request.json
    if database.delete_data("AlertsWatchlist", Symbol=req["alert_id"]):
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})


@app.route("/get_alerts", methods=["GET"])
def get_alerts():
    alerts = database.get_data_query("SELECT * FROM AlertsWatchlist")
    return jsonify(alerts)
