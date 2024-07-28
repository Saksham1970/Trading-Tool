from app_config import app
from flask import request, jsonify
from utils import database


@app.route("/get_watchlists", methods=["GET"])
def get_watchlists():
    try:
        watchlists = database.get_data("Watchlists", __dictionary=True)
        return jsonify({"success": True, "watchlists": watchlists}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/add_watchlist", methods=["POST"])
def add_watchlist():
    data = request.json
    watchlist_name = data.get("watchlist_name")
    symbols = data.get("symbols", [])

    if not watchlist_name:
        return jsonify({"success": False, "error": "Watchlist name is required"}), 400

    try:
        success = database.insert_data(
            "Watchlists", WatchlistName=watchlist_name, Symbols=symbols
        )
        if success:
            return (
                jsonify({"success": True, "message": "Watchlist added successfully"}),
                201,
            )
        else:
            return jsonify({"success": False, "error": "Failed to add watchlist"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/delete_watchlist", methods=["POST"])
def delete_watchlist():
    data = request.json
    watchlist_name = data.get("watchlist_name")

    if not watchlist_name:
        return jsonify({"success": False, "error": "Watchlist name is required"}), 400

    try:
        success = database.delete_data("Watchlists", WatchlistName=watchlist_name)
        if success:
            return (
                jsonify({"success": True, "message": "Watchlist deleted successfully"}),
                200,
            )
        else:
            return (
                jsonify({"success": False, "error": "Failed to delete watchlist"}),
                500,
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/add_watchlist_item", methods=["POST"])
def add_watchlist_item():
    data = request.json
    watchlist_name = data.get("watchlist_name")
    symbol = data.get("symbol")

    if not watchlist_name or not symbol:
        return (
            jsonify(
                {"success": False, "error": "Watchlist name and symbol are required"}
            ),
            400,
        )

    try:
        watchlist = database.get_data(
            "Watchlists", WatchlistName=watchlist_name, __dictionary=True
        )
        if not watchlist:
            return jsonify({"success": False, "error": "Watchlist not found"}), 404

        current_symbols = watchlist[0]["symbols"]
        if symbol not in current_symbols:
            current_symbols.append(symbol)
            success = database.insert_data(
                "Watchlists", WatchlistName=watchlist_name, Symbols=current_symbols
            )
            if success:
                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "Symbol added to watchlist successfully",
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {"success": False, "error": "Failed to add symbol to watchlist"}
                    ),
                    500,
                )
        else:
            return (
                jsonify({"success": True, "message": "Symbol already in watchlist"}),
                200,
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/delete_watchlist_item", methods=["POST"])
def delete_watchlist_item():
    data = request.json
    watchlist_name = data.get("watchlist_name")
    symbol = data.get("symbol")

    if not watchlist_name or not symbol:
        return (
            jsonify(
                {"success": False, "error": "Watchlist name and symbol are required"}
            ),
            400,
        )

    try:
        watchlist = database.get_data(
            "Watchlists", WatchlistName=watchlist_name, __dictionary=True
        )
        if not watchlist:
            return jsonify({"success": False, "error": "Watchlist not found"}), 404

        current_symbols = watchlist[0]["symbols"]
        if symbol in current_symbols:
            current_symbols.remove(symbol)
            success = database.insert_data(
                "Watchlists", WatchlistName=watchlist_name, Symbols=current_symbols
            )
            if success:
                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "Symbol removed from watchlist successfully",
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Failed to remove symbol from watchlist",
                        }
                    ),
                    500,
                )
        else:
            return jsonify({"success": True, "message": "Symbol not in watchlist"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
