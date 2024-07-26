from utils.startup import startup
from app_config import app, celery

# startup(cursor) # Commented out to avoid unnecessary data fetching
from pages.__init__ import *


@app.route("/")
def home():
    return "Flask is running", 200


if __name__ == "__main__":
    app.run(port=5000)
