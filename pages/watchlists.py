from app_config import app


@app.route("/get_watchlists", methods=["GET"])
def get_watchlists():
    NotImplemented


@app.route("/add_watchlist", methods=["POST"])
def add_watchlist():
    NotImplemented


@app.route("/delete_watchlist", methods=["POST"])
def delete_watchlist():
    NotImplemented


@app.route("/add_watchlist_item", methods=["POST"])
def add_watchlist_item():
    NotImplemented


@app.route("/delete_watchlist_item", methods=["POST"])
def delete_watchlist_item():
    NotImplemented
