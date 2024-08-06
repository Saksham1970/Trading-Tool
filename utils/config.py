import os
from datetime import datetime, timedelta
from utils.file_handling import load_json

# API parameters
API_CALLS = 50
API_RATE_LIMIT = 60


# Connection parameters
HOST = "timescaledb"
PORT = "5432"
DB = "stocksdb"
USER = "postgres"
PASSWORD = os.environ["POSTGRES_PASSWORD"]


# Settings
SETTINGS_FILE = "settings.json"
SETTINGS = load_json(SETTINGS_FILE)


# Constants related to data fetching
HOLIDAY_COMPENSATION_FACTOR = 1.2
REFERECE_DATETIME = datetime(2000, 1, 1)
MARKET_CLOSE_UPDATE_TD = timedelta(hours=1)
