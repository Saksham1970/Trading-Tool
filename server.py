from app_config import app
from utils.startup import startup

startup()  # Comment out to avoid unnecessary data fetching
from pages.__init__ import *


@app.route("/")
def home():
    return "Flask is running", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
