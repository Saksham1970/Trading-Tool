from flask import Flask
from flask_cors import CORS
from celery import Celery
from utils import database
from dotenv import load_dotenv

load_dotenv()

conn = database.connect_db()
if not conn:
    exit(1)
cursor = conn.cursor()

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL="redis://redis:6379/0",
    CELERY_RESULT_BACKEND="redis://redis:6379/0",
)

celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)
CORS(app)
