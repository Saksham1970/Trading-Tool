from flask import Flask, request, jsonify
from flask_cors import CORS

from dotenv import load_dotenv

import utils.database as database
from utils.startup import startup

load_dotenv()

conn = database.connect_db()
if not conn:
    exit(1)
cursor = conn.cursor()


app = Flask(__name__)
CORS(app)
startup(cursor)
from pages.extension import extension_receive

app.run(port=5000)


cursor.close()
conn.close()
