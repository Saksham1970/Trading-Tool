import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from dotenv import load_dotenv

load_dotenv()

from apscheduler.schedulers.background import BackgroundScheduler
from background_tasks import (
    download_daily_data,
    start_quote_streaming,
    update_averages,
    update_streamer_symbols,
)
import threading
from utils import database


scheduler = BackgroundScheduler()
scheduler.add_job(download_daily_data, "interval", hours=1)
scheduler.start()

exchanges = database.get_data_query("SELECT Exchange FROM ExchangeInfo")
for exchange in exchanges:
    update_averages(exchange[0])

quote_stream_thread = threading.Thread(target=start_quote_streaming)
update_streamer_thread = threading.Thread(target=update_streamer_symbols, daemon=True)

quote_stream_thread.start()
update_streamer_thread.start()

try:
    while True:
        pass
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    quote_stream_thread.join()
    update_streamer_thread.join()
